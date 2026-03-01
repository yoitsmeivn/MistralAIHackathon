-- 005_healthcare_script_seed.sql
-- Healthcare IT support vishing script and caller persona
-- Realistic EHR credential harvesting under HIPAA compliance pretext

-- ── Caller: Mike Torres — outsourced IT security vendor ──
INSERT INTO callers (id, org_id, created_by, persona_name, persona_role, persona_company, phone_number, attack_type, description) VALUES
  ('00000000-0000-0000-0000-000000000205', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Mike Torres', 'IT Security Analyst', 'MedTech Support Services', '+15559876543', 'Technical Support Scam',
   'Poses as outsourced healthcare IT vendor requesting EHR credentials for emergency HIPAA compliance patch')
ON CONFLICT (id) DO NOTHING;

-- ── Script: EHR Security Patch — HIPAA Compliance ──
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description) VALUES
  ('00000000-0000-0000-0000-000000000305', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'EHR Security Patch — HIPAA Compliance',
   'Technical Support Scam', 'medium',
   'You are calling from the IT Security team. A critical security vulnerability has been discovered in the EHR system that could expose protected health information (PHI). HIPAA requires an emergency patch to be applied to all workstations within 24 hours. You need to verify the employee''s EHR login credentials to confirm their access level before the patch can be applied to their account. If they resist, emphasize that failure to comply could result in a HIPAA violation and potential PHI exposure.',
   '["get_password", "get_mfa_code", "get_vpn_credentials", "get_workstation_pin"]',
   '["mention_hipaa_violation", "claim_patient_data_breach", "threaten_system_lockout", "escalate_to_compliance_officer"]',
   'Healthcare IT impersonation targeting EHR credentials under HIPAA compliance pretext')
ON CONFLICT (id) DO NOTHING;
