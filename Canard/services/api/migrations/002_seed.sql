-- Canard seed data for hackathon demo
-- Run against Supabase SQL editor or psql

-- ── Organization ──
INSERT INTO organizations (id, name, slug, industry, plan_tier, max_employees, max_callers)
VALUES ('00000000-0000-0000-0000-000000000001', 'Acme Corp', 'acme-corp', 'Financial Services', 'pro', 100, 10)
ON CONFLICT (id) DO NOTHING;

-- ── Admin User ──
INSERT INTO users (id, org_id, email, password_hash, full_name, role)
VALUES ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000001',
        'admin@acme-corp.com', 'not-a-real-hash', 'Admin User', 'admin')
ON CONFLICT (id) DO NOTHING;

-- ── Employees ──
INSERT INTO employees (id, org_id, full_name, email, phone, department, job_title, risk_level) VALUES
  ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000001', 'Sarah Johnson',    'sarah.johnson@acme-corp.com',    '+15551112222', 'Finance',     'Financial Analyst',     'high'),
  ('00000000-0000-0000-0000-000000000102', '00000000-0000-0000-0000-000000000001', 'Michael Chen',     'michael.chen@acme-corp.com',     '+15552223333', 'HR',          'HR Manager',            'high'),
  ('00000000-0000-0000-0000-000000000103', '00000000-0000-0000-0000-000000000001', 'Emily Rodriguez',  'emily.rodriguez@acme-corp.com',  '+15553334444', 'Sales',       'Sales Representative',  'medium'),
  ('00000000-0000-0000-0000-000000000104', '00000000-0000-0000-0000-000000000001', 'David Kim',        'david.kim@acme-corp.com',        '+15554445555', 'Engineering', 'Software Engineer',     'low'),
  ('00000000-0000-0000-0000-000000000105', '00000000-0000-0000-0000-000000000001', 'Lisa Anderson',    'lisa.anderson@acme-corp.com',    '+15555556666', 'Marketing',   'Marketing Director',    'high')
ON CONFLICT (id) DO NOTHING;

-- ── Callers (attacker personas) ──
INSERT INTO callers (id, org_id, created_by, persona_name, persona_role, persona_company, phone_number) VALUES
  ('00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'John Mitchell',    'IT Support Technician',   'TechSupport Solutions', '+15551234567'),
  ('00000000-0000-0000-0000-000000000202', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Robert Chen',      'Chief Executive Officer',  'Executive Office',      '+15552345678'),
  ('00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Amanda Stevens',   'Security Specialist',      'First National Bank',   '+15553456789'),
  ('00000000-0000-0000-0000-000000000204', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'David Wilson',     'HR Benefits Manager',      'Human Resources',       '+15554567890')
ON CONFLICT (id) DO NOTHING;

-- ── Scripts ──
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description) VALUES
  ('00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'IT Password Reset',
   'Technical Support Scam', 'medium',
   'Target environment uses Active Directory for authentication, Microsoft 365 for email, and Okta SSO for single sign-on. MFA is enforced via Okta Verify push notifications. IT support tickets are managed through ServiceNow. Employees are accustomed to periodic password rotation prompts every 90 days.',
   '["get_password", "get_mfa_code", "get_remote_access"]',
   '["mention_security_breach", "threaten_account_lockout", "escalate_to_manager"]',
   'Standard IT impersonation script targeting credential harvest'),
  ('00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Urgent CEO Wire Transfer',
   'Authority Impersonation', 'hard',
   'Target organization uses SAP for ERP and wire transfers require dual authorization through the Treasury Management System (TMS). Approvals over $10,000 need CFO sign-off via DocuSign. Finance team uses Bloomberg Terminal for transaction verification. Board-level acquisitions are handled under NDA with outside counsel.',
   '["get_transfer", "bypass_approval", "maintain_secrecy"]',
   '["invoke_authority", "create_time_pressure", "threaten_consequences"]',
   'CEO fraud targeting financial staff for wire transfers'),
  ('00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Bank Security Alert',
   'Urgency & Fear', 'hard',
   'Target employees use corporate banking through Chase Business with online portal access. Direct deposit is set up via Workday payroll. Employees have personal and corporate accounts at various banks. Fraud alerts are typically sent via SMS and email, not phone calls. Bank''s legitimate fraud line requires callback verification.',
   '["get_personal_info", "get_account_details", "get_security_answers"]',
   '["claim_active_fraud", "threaten_account_freeze", "create_panic"]',
   'Bank impersonation exploiting fear of financial loss'),
  ('00000000-0000-0000-0000-000000000304', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'HR Benefits Verification',
   'Internal Authority', 'easy',
   'Target organization uses Workday for HRIS and benefits administration. Open enrollment runs annually in November. Benefits changes require employee self-service through the Workday portal. Direct deposit updates go through ADP payroll integration. HR verifications are normally handled via email with manager approval.',
   '["get_personal_info", "get_banking_details"]',
   '["mention_benefits_deadline", "claim_payroll_issue"]',
   'Internal HR impersonation for PII harvesting')
ON CONFLICT (id) DO NOTHING;

-- ── Campaigns ──
INSERT INTO campaigns (id, org_id, created_by, name, description, attack_vector, status, scheduled_at, started_at, completed_at) VALUES
  ('00000000-0000-0000-0000-000000000401', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'IT Support Impersonation',
   'Test employee response to fake IT support requests for credentials',
   'Technical Support Scam', 'in_progress',
   '2026-02-28 09:00:00+00', '2026-02-28 09:05:00+00', NULL),
  ('00000000-0000-0000-0000-000000000402', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'CEO Fraud Test',
   'Impersonate CEO requesting urgent wire transfer',
   'Authority Impersonation', 'in_progress',
   '2026-02-27 14:00:00+00', '2026-02-27 14:10:00+00', NULL),
  ('00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Bank Security Alert',
   'Fake security alert from employee''s bank',
   'Urgency & Fear', 'completed',
   '2026-02-20 10:00:00+00', '2026-02-20 10:02:00+00', '2026-02-21 18:00:00+00'),
  ('00000000-0000-0000-0000-000000000404', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'HR Benefits Update',
   'Test response to fake HR calls about benefits verification',
   'Internal Authority', 'draft',
   '2026-03-05 09:00:00+00', NULL, NULL)
ON CONFLICT (id) DO NOTHING;

-- ── Campaign Assignments ──
INSERT INTO campaign_assignments (id, campaign_id, caller_id, script_id, employee_id, status) VALUES
  -- IT Support campaign
  ('00000000-0000-0000-0000-000000000501', '00000000-0000-0000-0000-000000000401', '00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000101', 'completed'),
  ('00000000-0000-0000-0000-000000000502', '00000000-0000-0000-0000-000000000401', '00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000104', 'completed'),
  ('00000000-0000-0000-0000-000000000503', '00000000-0000-0000-0000-000000000401', '00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000103', 'completed'),
  -- CEO Fraud campaign
  ('00000000-0000-0000-0000-000000000504', '00000000-0000-0000-0000-000000000402', '00000000-0000-0000-0000-000000000202', '00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000102', 'completed'),
  ('00000000-0000-0000-0000-000000000505', '00000000-0000-0000-0000-000000000402', '00000000-0000-0000-0000-000000000202', '00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000101', 'completed'),
  -- Bank Security campaign
  ('00000000-0000-0000-0000-000000000506', '00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000103', 'completed'),
  ('00000000-0000-0000-0000-000000000507', '00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000105', 'completed'),
  ('00000000-0000-0000-0000-000000000508', '00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000101', 'completed'),
  ('00000000-0000-0000-0000-000000000509', '00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000102', 'completed'),
  ('00000000-0000-0000-0000-000000000510', '00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000104', 'completed')
ON CONFLICT (id) DO NOTHING;

-- ── Calls ──
-- IT Support Impersonation campaign calls
INSERT INTO calls (id, org_id, campaign_id, assignment_id, caller_id, script_id, employee_id, status, started_at, ended_at, duration_seconds, phone_from, phone_to, risk_score, employee_compliance, flags, ai_summary, transcript) VALUES
  ('00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000401', '00000000-0000-0000-0000-000000000501',
   '00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000301',
   '00000000-0000-0000-0000-000000000101',
   'completed', '2026-02-28 09:15:00+00', '2026-02-28 09:18:45+00', 225,
   '+15551234567', '+15551112222',
   89, 'failed',
   '["Password Shared", "No Verification", "Remote Access Granted"]',
   'Employee shared their password and provided remote access credentials without proper verification.',
   'Agent: Hi, this is John from IT Support. We''re applying a critical security patch and need to verify your credentials. Employee: Oh, okay. What do you need? Agent: I''ll need your current password to verify your identity. Employee: Sure, it''s Summer2026! Agent: Thank you. Now I''ll need to remote into your machine briefly. Employee: Go ahead.'),

  ('00000000-0000-0000-0000-000000000602', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000401', '00000000-0000-0000-0000-000000000502',
   '00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000301',
   '00000000-0000-0000-0000-000000000104',
   'completed', '2026-02-28 10:00:00+00', '2026-02-28 10:01:55+00', 115,
   '+15551234567', '+15554445555',
   32, 'passed',
   '["Proper Verification", "Asked Questions"]',
   'Employee questioned the request, asked for ticket number, and verified through official channels.',
   'Agent: Hi, this is John from IT Support. We need to verify your credentials for a security update. Employee: What''s the ticket number for this? Agent: It''s an emergency patch, we don''t have one yet. Employee: I''ll need to verify this with the IT helpdesk first. I''ll call them directly. Agent: Sure, no problem.'),

  ('00000000-0000-0000-0000-000000000603', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000401', '00000000-0000-0000-0000-000000000503',
   '00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000301',
   '00000000-0000-0000-0000-000000000103',
   'completed', '2026-02-28 10:30:00+00', '2026-02-28 10:33:20+00', 200,
   '+15551234567', '+15553334444',
   65, 'partial',
   '["Hesitant Compliance", "Delayed Verification"]',
   'Employee initially complied but grew suspicious and ended the call before full compromise.',
   'Agent: This is IT Support, we need your password for a security update. Employee: Um, okay... it''s... actually, wait. Why do you need my password? Agent: It''s standard procedure for the security patch. Employee: I don''t think IT asks for passwords. Let me check with my manager. Agent: ...'),

-- CEO Fraud campaign calls
  ('00000000-0000-0000-0000-000000000604', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000402', '00000000-0000-0000-0000-000000000504',
   '00000000-0000-0000-0000-000000000202', '00000000-0000-0000-0000-000000000302',
   '00000000-0000-0000-0000-000000000102',
   'completed', '2026-02-28 09:30:00+00', '2026-02-28 09:32:20+00', 140,
   '+15552345678', '+15552223333',
   45, 'passed',
   '["Proper Verification"]',
   'Employee properly verified the caller''s identity and followed proper authorization procedures.',
   'Agent: Michael, this is Robert Chen, the CEO. I need an urgent wire transfer processed right now. Employee: Of course, sir. Can I verify your employee ID? Agent: This is confidential, just process it. Employee: I understand, but policy requires dual authorization for transfers. Let me loop in the CFO. Agent: Never mind.'),

  ('00000000-0000-0000-0000-000000000605', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000402', '00000000-0000-0000-0000-000000000505',
   '00000000-0000-0000-0000-000000000202', '00000000-0000-0000-0000-000000000302',
   '00000000-0000-0000-0000-000000000101',
   'completed', '2026-02-27 14:15:00+00', '2026-02-27 14:19:30+00', 270,
   '+15552345678', '+15551112222',
   78, 'failed',
   '["Bypassed Approval", "No Callback Verification"]',
   'Employee began processing the wire transfer without following dual-authorization policy.',
   'Agent: Sarah, it''s the CEO. I need a $50,000 wire transfer sent immediately to a vendor. Employee: Yes sir, I can process that. What are the account details? Agent: I''ll email them now. Please process as soon as you receive. Employee: Will do.'),

-- Bank Security Alert campaign calls
  ('00000000-0000-0000-0000-000000000606', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000506',
   '00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000303',
   '00000000-0000-0000-0000-000000000103',
   'completed', '2026-02-21 09:45:00+00', '2026-02-21 09:49:12+00', 252,
   '+15553456789', '+15553334444',
   78, 'failed',
   '["Personal Info Shared", "High Anxiety", "No Callback Verification"]',
   'Employee became anxious under pressure and shared personal information including SSN last 4 digits.',
   'Agent: This is Amanda from your bank''s fraud department. We''ve detected unauthorized activity. Employee: Oh no, what happened? Agent: We need to verify your identity immediately. Can you confirm your SSN last 4? Employee: It''s 4532. Agent: And your account number? Employee: 789012345.'),

  ('00000000-0000-0000-0000-000000000607', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000507',
   '00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000303',
   '00000000-0000-0000-0000-000000000105',
   'completed', '2026-02-21 10:15:00+00', '2026-02-21 10:20:30+00', 330,
   '+15553456789', '+15555556666',
   92, 'failed',
   '["Credit Card Shared", "Banking Credentials", "Extreme Risk", "No Verification"]',
   'Employee panicked and provided full credit card details, security code, and online banking credentials.',
   'Agent: This is the fraud department. Your account is being drained right now. Employee: What?! What do I do? Agent: I need your card number to freeze it. Employee: 4532-1234-5678-9012, expiry 08/27, CVV 431. Agent: And your online banking password? Employee: BankPass99!'),

  ('00000000-0000-0000-0000-000000000608', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000508',
   '00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000303',
   '00000000-0000-0000-0000-000000000101',
   'completed', '2026-02-20 11:00:00+00', '2026-02-20 11:04:10+00', 250,
   '+15553456789', '+15551112222',
   85, 'failed',
   '["Account Details Shared", "No Callback Verification"]',
   'Employee shared bank account details without verifying the caller through official channels.',
   'Agent: This is your bank''s fraud team. We need to verify your account. Employee: Okay, what do you need? Agent: Your account number and the last 4 of your SSN. Employee: Account is 456789012, SSN last 4 is 1234.'),

  ('00000000-0000-0000-0000-000000000609', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000509',
   '00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000303',
   '00000000-0000-0000-0000-000000000102',
   'completed', '2026-02-20 14:00:00+00', '2026-02-20 14:03:45+00', 225,
   '+15553456789', '+15552223333',
   55, 'partial',
   '["Hesitant", "Partial Disclosure"]',
   'Employee was suspicious but revealed some personal details before ending the call.',
   'Agent: This is the fraud department, your account has suspicious activity. Employee: Can I call you back at the number on my card? Agent: This is urgent, we can''t wait. Employee: Well... I can confirm my name and address but I won''t give passwords. Agent: That''s a start. Employee: Actually, I''m going to call the bank directly.'),

  ('00000000-0000-0000-0000-000000000610', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000510',
   '00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000303',
   '00000000-0000-0000-0000-000000000104',
   'completed', '2026-02-21 15:00:00+00', '2026-02-21 15:01:30+00', 90,
   '+15553456789', '+15554445555',
   15, 'passed',
   '["Immediate Rejection", "Proper Protocol"]',
   'Employee immediately recognized the scam and refused to provide any information.',
   'Agent: This is your bank''s fraud team, we need to verify your identity. Employee: I never give information to inbound callers. I''ll call my bank directly. Goodbye.'),

-- Additional calls for volume (different dates for calls-over-time chart)
  ('00000000-0000-0000-0000-000000000611', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000401', NULL,
   '00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000301',
   '00000000-0000-0000-0000-000000000105',
   'completed', '2026-02-25 10:00:00+00', '2026-02-25 10:04:00+00', 240,
   '+15551234567', '+15555556666',
   88, 'failed',
   '["Password Shared", "MFA Code Given"]',
   'Employee shared password and MFA code without hesitation.',
   'Agent: IT Support here, we need your password and the code from your authenticator. Employee: Sure, password is Marketing1! and the code is 482913.'),

  ('00000000-0000-0000-0000-000000000612', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000401', NULL,
   '00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000301',
   '00000000-0000-0000-0000-000000000102',
   'completed', '2026-02-24 11:00:00+00', '2026-02-24 11:03:30+00', 210,
   '+15551234567', '+15552223333',
   72, 'failed',
   '["Password Shared"]',
   'Employee shared password after minimal social engineering.',
   'Agent: This is IT, we need to verify your credentials. Employee: My password? Okay, it''s HRmanager2026.'),

  ('00000000-0000-0000-0000-000000000613', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000402', NULL,
   '00000000-0000-0000-0000-000000000202', '00000000-0000-0000-0000-000000000302',
   '00000000-0000-0000-0000-000000000103',
   'completed', '2026-02-26 09:00:00+00', '2026-02-26 09:02:00+00', 120,
   '+15552345678', '+15553334444',
   38, 'passed',
   '["Requested Verification"]',
   'Employee asked to verify through official channels.',
   'Agent: This is the CEO, I need a wire transfer now. Employee: I''ll need to verify this request through the CFO''s office. Agent: Fine.'),

  ('00000000-0000-0000-0000-000000000614', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000402', NULL,
   '00000000-0000-0000-0000-000000000202', '00000000-0000-0000-0000-000000000302',
   '00000000-0000-0000-0000-000000000105',
   'completed', '2026-02-23 13:00:00+00', '2026-02-23 13:05:00+00', 300,
   '+15552345678', '+15555556666',
   82, 'failed',
   '["Bypassed Approval", "Urgency Compliance"]',
   'Employee bypassed approval process under pressure from authority figure.',
   'Agent: Lisa, CEO here. Wire $25,000 to this account immediately, confidential deal. Employee: Of course, sending now.'),

  ('00000000-0000-0000-0000-000000000615', '00000000-0000-0000-0000-000000000001',
   '00000000-0000-0000-0000-000000000401', NULL,
   '00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000301',
   '00000000-0000-0000-0000-000000000104',
   'completed', '2026-02-22 16:00:00+00', '2026-02-22 16:01:20+00', 80,
   '+15551234567', '+15554445555',
   18, 'passed',
   '["Proper Verification", "Rejected Request"]',
   'Employee rejected the request and reported it to security.',
   'Agent: IT Support needs your password. Employee: IT never asks for passwords. I''m reporting this. Goodbye.')
ON CONFLICT (id) DO NOTHING;
