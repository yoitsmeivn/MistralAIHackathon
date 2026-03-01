-- 005_healthcare_script_seed.sql
-- Healthcare IT support vishing script and caller persona
-- Realistic EHR credential harvesting under HIPAA compliance pretext

-- ── Caller: Mike Torres — outsourced IT security vendor ──
INSERT INTO callers (id, org_id, created_by, persona_name, persona_role, persona_company, phone_number) VALUES
  ('00000000-0000-0000-0000-000000000205', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Mike Torres', 'IT Security Analyst', 'MedTech Support Services', '+15559876543')
ON CONFLICT (id) DO NOTHING;

-- ── Script: EHR Security Patch — HIPAA Compliance ──
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description) VALUES
  ('00000000-0000-0000-0000-000000000305', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'EHR Security Patch — HIPAA Compliance',
   'Technical Support Scam', 'medium',
   'Target facility runs Epic EHR on Citrix virtual desktops. Authentication is through Active Directory with Imprivata single sign-on at workstations. VPN access uses Cisco AnyConnect. The organization is HIPAA-regulated and underwent a compliance audit last quarter. Patch management is handled through SCCM with monthly maintenance windows. Workstation PINs are 6-digit codes used for Imprivata tap-and-go badges.',
   '["get_password", "get_mfa_code", "get_vpn_credentials", "get_workstation_pin"]',
   '["mention_hipaa_violation", "claim_patient_data_breach", "threaten_system_lockout", "escalate_to_compliance_officer"]',
   'Healthcare IT impersonation targeting EHR credentials under HIPAA compliance pretext')
ON CONFLICT (id) DO NOTHING;
