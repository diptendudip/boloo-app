"""
Routing Service - Auto-route cases to appropriate government entities

Matches grievances to the right office based on:
1. Issue type (taxonomy)
2. GPS location (nearest entity)
3. Entity competency
"""

from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_Distance, ST_SetSRID, ST_MakePoint

from app.models.case import Case
from app.models.entity import Entity
from app.models.taxonomy import Taxonomy


class RoutingService:
    """Service to route cases to appropriate government entities"""

    def __init__(self, db: Session):
        self.db = db

    def find_responsible_entity(
        self,
        issue_type_key: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_text: Optional[str] = None
    ) -> Tuple[Optional[Entity], float]:
        """
        Find the responsible entity for a case

        Args:
            issue_type_key: Taxonomy key (e.g., 'water_supply', 'road_damage')
            latitude: GPS latitude
            longitude: GPS longitude
            location_text: Text description of location

        Returns:
            Tuple of (Entity, confidence_score)
        """
        # Get taxonomy to find competent entities
        taxonomy = self.db.query(Taxonomy).filter(
            Taxonomy.key == issue_type_key,
            Taxonomy.type == "issue"
        ).first()

        if not taxonomy or not taxonomy.competent_entities:
            return None, 0.0

        # Get list of competent entity IDs
        competent_entity_ids = taxonomy.competent_entities

        # If we have GPS, find nearest competent entity
        if latitude and longitude:
            entity, distance = self._find_nearest_entity(
                competent_entity_ids,
                latitude,
                longitude
            )

            # Calculate confidence based on distance
            # High confidence if within 50km, lower as distance increases
            if distance is not None:
                if distance < 50000:  # < 50km
                    confidence = 0.9
                elif distance < 100000:  # < 100km
                    confidence = 0.7
                elif distance < 200000:  # < 200km
                    confidence = 0.5
                else:
                    confidence = 0.3
            else:
                confidence = 0.5

            return entity, confidence

        # If no GPS but have location text, try text matching
        elif location_text:
            entity = self._find_entity_by_location_text(
                competent_entity_ids,
                location_text
            )
            return entity, 0.6 if entity else 0.0

        # Fallback: Return first competent entity (district level preferred)
        else:
            entity = self.db.query(Entity).filter(
                Entity.id.in_(competent_entity_ids),
                Entity.type == "district"
            ).first()

            if not entity:
                entity = self.db.query(Entity).filter(
                    Entity.id.in_(competent_entity_ids)
                ).first()

            return entity, 0.3 if entity else 0.0

    def _find_nearest_entity(
        self,
        entity_ids: list,
        latitude: float,
        longitude: float
    ) -> Tuple[Optional[Entity], Optional[float]]:
        """
        Find nearest entity from a list of IDs using PostGIS

        Args:
            entity_ids: List of entity UUIDs
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            Tuple of (Entity, distance_in_meters)
        """
        # Create point geometry (SRID 4326 is WGS84 - standard GPS)
        point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

        # Query for nearest entity
        result = self.db.query(
            Entity,
            ST_Distance(
                func.cast(Entity.location, Geometry),
                point,
                True  # Use sphere for accurate distance in meters
            ).label('distance')
        ).filter(
            Entity.id.in_(entity_ids),
            Entity.location.isnot(None)
        ).order_by(
            'distance'
        ).first()

        if result:
            return result.Entity, result.distance
        return None, None

    def _find_entity_by_location_text(
        self,
        entity_ids: list,
        location_text: str
    ) -> Optional[Entity]:
        """
        Find entity by matching location text

        Args:
            entity_ids: List of entity UUIDs
            location_text: Location description (village/ward name)

        Returns:
            Matched entity or None
        """
        location_lower = location_text.lower()

        # Try exact match on name first
        entity = self.db.query(Entity).filter(
            Entity.id.in_(entity_ids),
            func.lower(Entity.name).contains(location_lower)
        ).first()

        if entity:
            return entity

        # Try metadata match (village name, district name, etc.)
        entities = self.db.query(Entity).filter(
            Entity.id.in_(entity_ids)
        ).all()

        for entity in entities:
            if entity.metadata:
                # Check if location text appears in metadata
                metadata_str = str(entity.metadata).lower()
                if location_lower in metadata_str:
                    return entity

        return None

    def get_escalation_entity(self, current_entity: Entity) -> Optional[Entity]:
        """
        Get the next escalation level entity

        Escalation path: GP → Block → District → Department

        Args:
            current_entity: Current responsible entity

        Returns:
            Next level entity or None if at top level
        """
        if not current_entity.parent_entity_id:
            return None

        return self.db.query(Entity).filter(
            Entity.id == current_entity.parent_entity_id
        ).first()

    def get_sla_hours(self, entity: Entity) -> int:
        """
        Get SLA hours for an entity type

        Args:
            entity: Government entity

        Returns:
            SLA hours (default 72)
        """
        sla_mapping = {
            "gp": 72,       # Gram Panchayat: 3 days
            "block": 96,    # Block: 4 days
            "district": 120, # District: 5 days
            "dept": 168,    # Department: 7 days
            "state": 240,   # State: 10 days
        }

        return sla_mapping.get(entity.type, 72)

    def validate_routing(
        self,
        case: Case,
        proposed_entity: Entity
    ) -> Tuple[bool, str]:
        """
        Validate if routing is appropriate

        Args:
            case: The case being routed
            proposed_entity: Proposed responsible entity

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check if entity is active
        if proposed_entity.metadata and not proposed_entity.metadata.get("is_active", True):
            return False, "Entity is not active"

        # Check if entity has required contact info
        if not proposed_entity.contact_email and not proposed_entity.contact_phone:
            return False, "Entity has no contact information"

        # Check geographic proximity if GPS available
        if case.location and proposed_entity.location:
            point = ST_SetSRID(ST_MakePoint(case.location.x, case.location.y), 4326)

            distance = self.db.query(
                ST_Distance(
                    func.cast(proposed_entity.location, Geometry),
                    point,
                    True
                )
            ).scalar()

            # Warn if entity is very far (> 500km)
            if distance and distance > 500000:
                return True, f"Warning: Entity is {int(distance/1000)}km away"

        return True, "Valid routing"


def create_routing_service(db: Session) -> RoutingService:
    """Factory function to create routing service"""
    return RoutingService(db)
