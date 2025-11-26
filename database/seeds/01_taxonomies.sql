-- Issue Taxonomies for Indian Civic Grievances
-- Insert comprehensive list of grievance categories

-- Water Supply Issues
INSERT INTO taxonomies (type, key, label_en, label_hi, metadata) VALUES
('issue', 'water_supply', 'Water Supply', 'जल आपूर्ति', '{"competent_entities": ["gp", "district"]}'),
('issue', 'water_contamination', 'Water Contamination', 'जल प्रदूषण', '{"competent_entities": ["gp", "dept"], "parent": "water_supply"}'),
('issue', 'water_shortage', 'Water Shortage', 'पानी की कमी', '{"competent_entities": ["gp", "district"], "parent": "water_supply"}'),
('issue', 'water_pipeline', 'Pipeline Leakage/Damage', 'पाइपलाइन रिसाव/क्षति', '{"competent_entities": ["gp"], "parent": "water_supply"}'),

-- Road Issues
('issue', 'roads', 'Roads and Infrastructure', 'सड़क और बुनियादी ढांचा', '{"competent_entities": ["gp", "block", "district"]}'),
('issue', 'road_damage', 'Road Damage/Potholes', 'सड़क क्षति/गड्ढे', '{"competent_entities": ["gp", "block"], "parent": "roads"}'),
('issue', 'road_construction', 'Road Construction Issues', 'सड़क निर्माण समस्याएं', '{"competent_entities": ["block", "district"], "parent": "roads"}'),
('issue', 'road_drainage', 'Drainage Problems', 'जल निकासी की समस्याएं', '{"competent_entities": ["gp"], "parent": "roads"}'),

-- Electricity Issues
('issue', 'electricity', 'Electricity', 'बिजली', '{"competent_entities": ["dept", "district"]}'),
('issue', 'power_outage', 'Power Outage', 'बिजली की कटौती', '{"competent_entities": ["dept"], "parent": "electricity"}'),
('issue', 'power_line_damage', 'Power Line Damage', 'बिजली लाइन क्षति', '{"competent_entities": ["dept"], "parent": "electricity"}'),
('issue', 'meter_issue', 'Meter Issues/Billing', 'मीटर समस्याएं/बिलिंग', '{"competent_entities": ["dept"], "parent": "electricity"}'),

-- Sanitation Issues
('issue', 'sanitation', 'Sanitation and Hygiene', 'स्वच्छता', '{"competent_entities": ["gp", "block"]}'),
('issue', 'garbage_collection', 'Garbage Collection', 'कचरा संग्रहण', '{"competent_entities": ["gp"], "parent": "sanitation"}'),
('issue', 'open_defecation', 'Open Defecation', 'खुले में शौच', '{"competent_entities": ["gp"], "parent": "sanitation"}'),
('issue', 'toilet_construction', 'Toilet Construction', 'शौचालय निर्माण', '{"competent_entities": ["gp", "block"], "parent": "sanitation"}'),
('issue', 'drainage_blockage', 'Drainage Blockage', 'नाली अवरोध', '{"competent_entities": ["gp"], "parent": "sanitation"}'),

-- NREGA (MGNREGA) Issues
('issue', 'nrega', 'NREGA/MGNREGA', 'नरेगा/मनरेगा', '{"competent_entities": ["block", "district"]}'),
('issue', 'nrega_job_card', 'Job Card Issues', 'जॉब कार्ड समस्याएं', '{"competent_entities": ["block"], "parent": "nrega"}'),
('issue', 'nrega_payment', 'Payment Delays', 'भुगतान में देरी', '{"competent_entities": ["block", "district"], "parent": "nrega"}'),
('issue', 'nrega_work_demand', 'Work Demand Not Met', 'काम की मांग पूरी नहीं', '{"competent_entities": ["block"], "parent": "nrega"}'),
('issue', 'nrega_corruption', 'Corruption/Malpractice', 'भ्रष्टाचार/कदाचार', '{"competent_entities": ["district"], "parent": "nrega"}'),

-- Pension Issues
('issue', 'pension', 'Pension and Social Security', 'पेंशन और सामाजिक सुरक्षा', '{"competent_entities": ["block", "district"]}'),
('issue', 'pension_old_age', 'Old Age Pension', 'वृद्धावस्था पेंशन', '{"competent_entities": ["block"], "parent": "pension"}'),
('issue', 'pension_widow', 'Widow Pension', 'विधवा पेंशन', '{"competent_entities": ["block"], "parent": "pension"}'),
('issue', 'pension_disability', 'Disability Pension', 'विकलांगता पेंशन', '{"competent_entities": ["block"], "parent": "pension"}'),
('issue', 'pension_delay', 'Pension Payment Delay', 'पेंशन भुगतान में देरी', '{"competent_entities": ["block", "district"], "parent": "pension"}'),

-- Healthcare Issues
('issue', 'healthcare', 'Healthcare Services', 'स्वास्थ्य सेवाएं', '{"competent_entities": ["block", "district", "dept"]}'),
('issue', 'hospital_staff', 'Staff Shortage/Absence', 'कर्मचारियों की कमी/अनुपस्थिति', '{"competent_entities": ["block", "district"], "parent": "healthcare"}'),
('issue', 'medicine_shortage', 'Medicine Shortage', 'दवा की कमी', '{"competent_entities": ["block", "district"], "parent": "healthcare"}'),
('issue', 'healthcare_facility', 'Facility Issues', 'सुविधा समस्याएं', '{"competent_entities": ["block", "district"], "parent": "healthcare"}'),

-- Education Issues
('issue', 'education', 'Education', 'शिक्षा', '{"competent_entities": ["block", "district", "dept"]}'),
('issue', 'school_infrastructure', 'School Infrastructure', 'स्कूल बुनियादी ढांचा', '{"competent_entities": ["block"], "parent": "education"}'),
('issue', 'teacher_absence', 'Teacher Absence', 'शिक्षक अनुपस्थिति', '{"competent_entities": ["block", "district"], "parent": "education"}'),
('issue', 'midday_meal', 'Mid-Day Meal Issues', 'मध्याह्न भोजन समस्याएं', '{"competent_entities": ["block"], "parent": "education"}'),
('issue', 'school_scholarship', 'Scholarship Issues', 'छात्रवृत्ति समस्याएं', '{"competent_entities": ["block", "district"], "parent": "education"}'),

-- Public Distribution System (PDS)
('issue', 'pds', 'Public Distribution System', 'सार्वजनिक वितरण प्रणाली', '{"competent_entities": ["block", "district"]}'),
('issue', 'ration_card', 'Ration Card Issues', 'राशन कार्ड समस्याएं', '{"competent_entities": ["block"], "parent": "pds"}'),
('issue', 'ration_quality', 'Ration Quality', 'राशन की गुणवत्ता', '{"competent_entities": ["block"], "parent": "pds"}'),
('issue', 'ration_quantity', 'Ration Quantity Shortage', 'राशन की मात्रा कम', '{"competent_entities": ["block"], "parent": "pds"}'),

-- Land and Property Issues
('issue', 'land', 'Land and Property', 'भूमि और संपत्ति', '{"competent_entities": ["block", "district"]}'),
('issue', 'land_records', 'Land Records Issues', 'भूमि रिकॉर्ड समस्याएं', '{"competent_entities": ["block", "district"], "parent": "land"}'),
('issue', 'land_dispute', 'Land Dispute', 'भूमि विवाद', '{"competent_entities": ["block", "district"], "parent": "land"}'),
('issue', 'property_tax', 'Property Tax Issues', 'संपत्ति कर समस्याएं', '{"competent_entities": ["gp", "block"], "parent": "land"}'),

-- Agriculture Issues
('issue', 'agriculture', 'Agriculture', 'कृषि', '{"competent_entities": ["block", "district", "dept"]}'),
('issue', 'crop_insurance', 'Crop Insurance', 'फसल बीमा', '{"competent_entities": ["block", "district"], "parent": "agriculture"}'),
('issue', 'fertilizer', 'Fertilizer Issues', 'उर्वरक समस्याएं', '{"competent_entities": ["block"], "parent": "agriculture"}'),
('issue', 'irrigation', 'Irrigation Issues', 'सिंचाई समस्याएं', '{"competent_entities": ["gp", "block"], "parent": "agriculture"}'),
('issue', 'farm_loan', 'Farm Loan Issues', 'कृषि ऋण समस्याएं', '{"competent_entities": ["block", "district"], "parent": "agriculture"}'),

-- Police and Safety
('issue', 'police', 'Police and Public Safety', 'पुलिस और सार्वजनिक सुरक्षा', '{"competent_entities": ["district", "dept"]}'),
('issue', 'crime', 'Crime/Violence', 'अपराध/हिंसा', '{"competent_entities": ["district"], "parent": "police"}'),
('issue', 'police_inaction', 'Police Inaction', 'पुलिस निष्क्रियता', '{"competent_entities": ["district"], "parent": "police"}'),

-- Other Issues
('issue', 'corruption', 'Corruption', 'भ्रष्टाचार', '{"competent_entities": ["block", "district"]}'),
('issue', 'document_issues', 'Document/Certificate Issues', 'दस्तावेज़/प्रमाण पत्र समस्याएं', '{"competent_entities": ["block", "gp"]}'),
('issue', 'caste_certificate', 'Caste Certificate', 'जाति प्रमाण पत्र', '{"competent_entities": ["block"], "parent": "document_issues"}'),
('issue', 'income_certificate', 'Income Certificate', 'आय प्रमाण पत्र', '{"competent_entities": ["block"], "parent": "document_issues"}'),
('issue', 'birth_death_certificate', 'Birth/Death Certificate', 'जन्म/मृत्यु प्रमाण पत्र', '{"competent_entities": ["gp", "block"], "parent": "document_issues"}'),
('issue', 'other', 'Other Issues', 'अन्य समस्याएं', '{"competent_entities": ["gp", "block", "district"]}');

-- Topic Taxonomies for Community Content (Phase 2)
INSERT INTO taxonomies (type, key, label_en, label_hi, metadata) VALUES
('topic', 'story', 'Story', 'कहानी', '{}'),
('topic', 'song', 'Song', 'गीत', '{}'),
('topic', 'knowledge', 'Knowledge', 'ज्ञान', '{}'),
('topic', 'tradition', 'Tradition', 'परंपरा', '{}'),
('topic', 'festival', 'Festival', 'त्योहार', '{}'),
('topic', 'agriculture_tips', 'Agriculture Tips', 'कृषि सुझाव', '{}'),
('topic', 'health_tips', 'Health Tips', 'स्वास्थ्य सुझाव', '{}');

COMMIT;
