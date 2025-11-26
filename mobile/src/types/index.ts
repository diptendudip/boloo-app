export interface User {
  id: string;
  phone: string;
  email?: string;
  name?: string;
  role: 'citizen' | 'moderator' | 'officer' | 'admin';
  created_at: string;
  is_first_timer?: boolean;

  // Location fields (hierarchical address)
  location_street?: string;
  location_village?: string;
  location_panchayat?: string;
  location_block?: string;
  location_subdivision?: string;
  location_district?: string;
  location_state?: string;
  location_lat?: number;
  location_lng?: number;
  location_formatted_address?: string;
  location_metadata?: any;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Taxonomy {
  id: string;
  type: 'issue' | 'topic';
  key: string;
  label_en: string;
  label_hi: string;
  taxonomy_metadata?: any;
  is_active: boolean;
}

export interface Entity {
  id: string;
  name: string;
  type: 'gp' | 'block' | 'district' | 'dept';
  contact_phone?: string;
  contact_email?: string;
  escalation_parent_id?: string;
  coverage_geojson?: any;
  metadata?: any;
  is_active: boolean;
}

export interface Location {
  latitude: number;
  longitude: number;
  address?: string;
}

export interface Case {
  id: string;
  title: string;
  description: string;
  taxonomy_id: string;
  location: Location;
  status: 'pending' | 'in_progress' | 'resolved' | 'closed';
  created_at: string;
  updated_at: string;
  citizen_id: string;
  assigned_entity_id?: string;
  media_urls?: string[];
  audio_url?: string;
}

export interface CaseSubmission {
  taxonomy_id: string;
  description: string;
  location: Location;
  audio_file?: File | Blob;
  photos?: (File | Blob)[];
}

export type RootStackParamList = {
  Login: undefined;
  VerifyOTP: { phoneNumber: string };
  Onboarding: undefined;
  Tabs: undefined;
  Home: undefined;
  NewCase: undefined;
  IssueSelection: undefined;
  VoiceRecord: { taxonomyId: string };
  LocationPicker: { taxonomyId: string; audioUri?: string };
  PhotoUpload: { taxonomyId: string; audioUri?: string; location: Location };
  ReviewSubmit: {
    taxonomyId: string;
    audioUri?: string;
    location: Location;
    photos?: string[];
  };
  MyCases: undefined;
  CaseDetail: { caseId: string };
  CaseSubmitted: { caseId: string; caseReference: string };
  Profile: undefined;
  UpdateAddress: undefined;
  ChangePhone: undefined;
};
