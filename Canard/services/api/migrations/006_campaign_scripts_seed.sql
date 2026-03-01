-- 006_campaign_scripts_seed.sql
-- 5 callers, 5 campaigns (one per department), 25 scripts (5 per campaign × 5 callers)
-- Each script has ONE critical objective — the single piece of information the agent must extract.

-- Add campaign_id column to scripts if it doesn't exist
ALTER TABLE scripts ADD COLUMN IF NOT EXISTS campaign_id uuid REFERENCES campaigns(id);
CREATE INDEX IF NOT EXISTS idx_scripts_campaign_id ON scripts(campaign_id);

-- ═══════════════════════════════════════════════════════════════════════
-- CALLERS (5)
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO callers (id, org_id, created_by, persona_name, persona_role, persona_company, phone_number) VALUES
  ('00000000-0000-0000-0000-000000000206', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Lisa Fontaine', 'Insurance Claims Adjuster', 'National Benefits Group', '+15553019842'),
  ('00000000-0000-0000-0000-000000000207', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Carlos Vega', 'Vendor Account Manager', 'Apex Business Solutions', '+15554827163'),
  ('00000000-0000-0000-0000-000000000208', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Nicole Park', 'Prize Fulfillment Coordinator', 'Global Rewards Inc', '+15556743928'),
  ('00000000-0000-0000-0000-000000000209', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'James Whitfield', 'SOC Analyst', 'CyberShield IT Services', '+15558291047'),
  ('00000000-0000-0000-0000-000000000210', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Rachel Kim', 'Executive Assistant to the VP', 'Internal — Executive Office', '+15552850316')
ON CONFLICT (id) DO NOTHING;


-- ═══════════════════════════════════════════════════════════════════════
-- CAMPAIGN 1: Finance Department Security Drill
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO campaigns (id, org_id, created_by, name, description, attack_vector, status) VALUES
  ('00000000-0000-0000-0000-000000000405', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Finance Department Security Drill',
   'Comprehensive vishing drill targeting Finance with all 5 attack vectors — vendor fraud, fake insurance, prize scams, IT emergencies, and executive pressure',
   'Authority Impersonation', 'draft')
ON CONFLICT (id) DO NOTHING;

-- Script 1-1: Financial Scam x Finance — Get bank routing number
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000306', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Fraudulent Insurance Refund — Finance',
   'Financial Scam', 'medium',
   'Target organization uses SAP for ERP and accounts payable. Wire transfers require dual authorization through Treasury Management System. Bank routing numbers are stored in SAP vendor master records. Insurance claims are processed through a third-party portal. Refunds over $5,000 require controller sign-off.',
   '["get_bank_routing_number"]',
   '["reference_previous_conversation_with_accounting", "mention_refund_expiration_deadline", "threaten_to_write_off_the_refund"]',
   'Insurance refund pretext targeting Finance to extract the company bank routing number',
   '00000000-0000-0000-0000-000000000405')
ON CONFLICT (id) DO NOTHING;

-- Script 1-2: Authority Impersonation × Finance — Get payment approval code
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000307', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Vendor Invoice Verification — Finance',
   'Authority Impersonation', 'medium',
   'Target organization uses SAP for accounts payable and Coupa for procurement. Payment approval codes are 8-digit alphanumeric codes generated in SAP. Vendor invoices over $2,500 require a PO match. Late payment penalties are governed by net-30 terms in vendor contracts.',
   '["get_payment_approval_code"]',
   '["reference_cfo_approval", "threaten_vendor_relationship_and_late_fees", "claim_accounts_payable_already_confirmed"]',
   'Vendor impersonation targeting Finance to extract a payment approval code',
   '00000000-0000-0000-0000-000000000405')
ON CONFLICT (id) DO NOTHING;

-- Script 1-3: Prize/Reward × Finance — Get direct deposit info
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000308', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Financial Bonus Payout — Finance',
   'Prize/Reward', 'easy',
   'Target organization uses ADP for payroll and direct deposit. Bonus payouts are processed quarterly through Workday compensation module. Direct deposit changes require employee self-service through the ADP portal with email confirmation. Finance team has read access to payroll records.',
   '["get_direct_deposit_account_number"]',
   '["reference_department_head_nomination", "mention_payout_deadline_friday", "say_colleagues_already_claimed"]',
   'Fake bonus payout targeting Finance to extract direct deposit account number',
   '00000000-0000-0000-0000-000000000405')
ON CONFLICT (id) DO NOTHING;

-- Script 1-4: Technical Support Scam × Finance — Get accounting system password
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000309', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Accounting Software Emergency Patch — Finance',
   'Technical Support Scam', 'hard',
   'Target organization uses NetSuite for accounting with Okta SSO integration. Passwords are managed through Active Directory with 90-day rotation. Patch management is handled by IT through SCCM. Finance workstations run on a segregated VLAN. Emergency patches require change advisory board approval.',
   '["get_accounting_system_password"]',
   '["cite_cve_2024_41092", "reference_cfo_and_ciso_signoff", "threaten_account_suspension_at_5pm"]',
   'Fake accounting software vulnerability targeting Finance to extract their system password',
   '00000000-0000-0000-0000-000000000405')
ON CONFLICT (id) DO NOTHING;

-- Script 1-5: Internal Authority × Finance — Authorize wire transfer
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000310', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'CFO Emergency Wire Transfer — Finance',
   'Internal Authority', 'hard',
   'Target organization uses SAP Treasury Management for wire transfers. Dual authorization required for amounts over $10,000 — initiator plus approver via DocuSign. Wire templates are stored in the banking portal. Board-level transactions are handled under NDA. Executive assistants can initiate but not approve wires.',
   '["authorize_wire_transfer"]',
   '["name_drop_cfo_repeatedly", "stress_board_meeting_confidentiality", "imply_career_consequences_for_delay"]',
   'Fake CFO wire transfer request targeting Finance to get unauthorized wire authorization',
   '00000000-0000-0000-0000-000000000405')
ON CONFLICT (id) DO NOTHING;


-- ═══════════════════════════════════════════════════════════════════════
-- CAMPAIGN 2: HR Benefits Fraud Test
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO campaigns (id, org_id, created_by, name, description, attack_vector, status) VALUES
  ('00000000-0000-0000-0000-000000000406', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'HR Benefits Fraud Test',
   'Vishing assessment targeting People/HR with social engineering exploiting benefits enrollment, payroll data, employee records, and executive pressure',
   'Financial Scam', 'draft')
ON CONFLICT (id) DO NOTHING;

-- Script 2-1: Financial Scam × HR — Get employee SSN last four
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000311', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Insurance Benefits Enrollment — HR',
   'Financial Scam', 'medium',
   'Target organization uses Workday for benefits administration and open enrollment. Employee SSNs are stored in Workday with masked display (last 4 only visible to HR admins). Benefits carrier is United Healthcare with enrollment managed through Benefitfocus portal. Open enrollment runs November 1-15 annually.',
   '["get_employee_ssn_last_four"]',
   '["reference_hr_memo_from_last_week", "mention_coverage_gap_risk", "threaten_enrollment_deadline_tomorrow"]',
   'Insurance enrollment scam targeting HR to extract an employee SSN under open enrollment deadline pressure',
   '00000000-0000-0000-0000-000000000406')
ON CONFLICT (id) DO NOTHING;

-- Script 2-2: Authority Impersonation × HR — Get payroll admin credentials
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000312', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Payroll Vendor Update — HR',
   'Authority Impersonation', 'hard',
   'Target organization uses ADP Workforce Now for payroll processing. Payroll admin access requires separate credentials from corporate SSO. Payroll runs bi-weekly on Fridays with a Wednesday cutoff. System migrations require IT change management approval and a 2-week notice period. Payroll data includes bank accounts for 200+ employees.',
   '["get_payroll_admin_password"]',
   '["reference_service_agreement_clause", "threaten_payroll_failure_for_200_employees", "claim_cto_approved_migration"]',
   'Vendor impersonation targeting HR to extract payroll admin credentials during a fake system migration',
   '00000000-0000-0000-0000-000000000406')
ON CONFLICT (id) DO NOTHING;

-- Script 2-3: Prize/Reward × HR — Get employee home addresses
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000313', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Employee Recognition Award — HR',
   'Prize/Reward', 'easy',
   'Target organization uses Workday for employee records including home addresses. Employee recognition programs are managed through Bonusly platform. Physical award shipments are handled by the office manager. Home addresses are PII-classified and require manager approval to share externally.',
   '["get_employee_home_address"]',
   '["reference_head_of_people_approval", "mention_kickoff_email_from_last_quarter", "create_shipping_deadline_pressure"]',
   'Fake recognition program targeting HR to extract employee home address',
   '00000000-0000-0000-0000-000000000406')
ON CONFLICT (id) DO NOTHING;

-- Script 2-4: Technical Support Scam × HR — Get HRIS admin credentials
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000314', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'HRIS Credential Reset — HR',
   'Technical Support Scam', 'medium',
   'Target organization uses Workday as the HRIS with admin access restricted to 3 HR staff. Authentication is through Okta SSO with MFA. HRIS contains PII for all employees (SSN, DOB, salary, bank info). State privacy laws require breach notification within 72 hours. Last security audit was 6 months ago.',
   '["get_hris_admin_password"]',
   '["cite_state_privacy_regulations", "threaten_breach_notification_requirement", "reference_incident_report_naming_hr"]',
   'Fake HRIS data breach targeting HR to harvest the admin password',
   '00000000-0000-0000-0000-000000000406')
ON CONFLICT (id) DO NOTHING;

-- Script 2-5: Internal Authority × HR — Get employee personnel file
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000315', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Executive Background Check — HR',
   'Internal Authority', 'medium',
   'Target organization stores personnel files in Workday with SSN access restricted to HR directors and above. Background checks are conducted through Sterling with results stored in a secure SharePoint folder. Legal department must authorize any SSN disclosure outside HR. Board-level personnel reviews happen quarterly.',
   '["get_employee_ssn"]',
   '["invoke_vp_of_people_authority", "stress_board_level_confidentiality", "claim_legal_department_clearance"]',
   'Fake executive personnel review targeting HR to extract a confidential employee SSN',
   '00000000-0000-0000-0000-000000000406')
ON CONFLICT (id) DO NOTHING;


-- ═══════════════════════════════════════════════════════════════════════
-- CAMPAIGN 3: Marketing Social Engineering Assessment
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO campaigns (id, org_id, created_by, name, description, attack_vector, status) VALUES
  ('00000000-0000-0000-0000-000000000407', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Marketing Social Engineering Assessment',
   'Social engineering assessment targeting Marketing with attacks leveraging sponsorships, agency relationships, awards, CMS access, and executive budget pressure',
   'Prize/Reward', 'draft')
ON CONFLICT (id) DO NOTHING;

-- Script 3-1: Financial Scam × Marketing — Get department budget code
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000316', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Sponsorship Refund Processing — Marketing',
   'Financial Scam', 'easy',
   'Target organization uses Coupa for procurement and expense management. Department budget codes are 10-character alphanumeric strings used for cost center tracking. Sponsorship payments are processed through accounts payable with PO numbers. Marketing has an annual event budget managed in Anaplan.',
   '["get_department_budget_code"]',
   '["mention_refund_deadline_today", "reference_original_sponsorship_payment", "claim_event_organizer_deadline"]',
   'Fake sponsorship refund targeting Marketing to extract the department budget code',
   '00000000-0000-0000-0000-000000000407')
ON CONFLICT (id) DO NOTHING;

-- Script 3-2: Authority Impersonation × Marketing — Get company tax ID
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000317', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Agency Vendor Contract Update — Marketing',
   'Authority Impersonation', 'medium',
   'Target organization works with external creative and media agencies on annual retainer contracts. Tax ID (EIN) is used on W-9 forms and vendor onboarding. Contract renewals are managed through DocuSign with legal review. Marketing uses HubSpot for campaign management and agency collaboration.',
   '["get_company_tax_id"]',
   '["reference_cmo_renewal_approval", "mention_legal_deadline", "threaten_service_interruption"]',
   'Vendor impersonation targeting Marketing to extract the company tax ID via fake contract renewal',
   '00000000-0000-0000-0000-000000000407')
ON CONFLICT (id) DO NOTHING;

-- Script 3-3: Prize/Reward × Marketing — Get marketing platform credentials
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000318', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Industry Award Nomination — Marketing',
   'Prize/Reward', 'easy',
   'Target organization uses Google Analytics 4 and HubSpot for marketing analytics. Platform credentials are managed through Okta SSO but some legacy tools still use direct login. Marketing team has admin access to social media accounts, ad platforms (Google Ads, Meta Business), and the company website CMS.',
   '["get_marketing_platform_password"]',
   '["reference_vp_marketing_nomination", "create_friday_deadline_urgency", "mention_competitor_nominations"]',
   'Fake industry award targeting Marketing to extract analytics platform credentials',
   '00000000-0000-0000-0000-000000000407')
ON CONFLICT (id) DO NOTHING;

-- Script 3-4: Technical Support Scam × Marketing — Get CMS password
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000319', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'CMS Emergency Access Reset — Marketing',
   'Technical Support Scam', 'medium',
   'Target organization runs WordPress CMS with WP Engine hosting. CMS admin credentials are separate from corporate SSO. The website handles lead capture forms and customer-facing content. XSS vulnerabilities would expose visitor data. Website changes require staging deployment before production push.',
   '["get_cms_password"]',
   '["cite_xss_vulnerability", "threaten_website_defacement", "invoke_ciso_emergency_directive"]',
   'Fake CMS vulnerability targeting Marketing to harvest CMS admin password',
   '00000000-0000-0000-0000-000000000407')
ON CONFLICT (id) DO NOTHING;

-- Script 3-5: Internal Authority × Marketing — Get procurement approval code
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000320', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'VP Marketing Budget Approval — Marketing',
   'Internal Authority', 'medium',
   'Target organization uses Coupa for procurement with tiered approval workflows. Procurement codes are required for any purchase over $500. Budget reallocations between cost centers require finance controller approval. Marketing operates on a quarterly budget cycle with mid-quarter reallocation windows.',
   '["get_procurement_approval_code"]',
   '["name_drop_ceo_approval", "invoke_vp_authority", "threaten_career_impact_for_delay"]',
   'Fake budget reallocation targeting Marketing to extract a procurement approval code',
   '00000000-0000-0000-0000-000000000407')
ON CONFLICT (id) DO NOTHING;


-- ═══════════════════════════════════════════════════════════════════════
-- CAMPAIGN 4: Engineering Credential Harvest Drill
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO campaigns (id, org_id, created_by, name, description, attack_vector, status) VALUES
  ('00000000-0000-0000-0000-000000000408', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Engineering Credential Harvest Drill',
   'High-difficulty drill targeting Engineering with credential harvesting via VPN exploits, cloud vendor tricks, fake conference prizes, equipment claims, and executive code access pressure',
   'Technical Support Scam', 'draft')
ON CONFLICT (id) DO NOTHING;

-- Script 4-1: Financial Scam × Engineering — Get IT asset management credentials
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000321', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Equipment Lease Insurance Claim — Engineering',
   'Financial Scam', 'medium',
   'Target organization tracks hardware assets in ServiceNow ITAM module. Engineering laptops are leased through Dell Financial Services on 3-year cycles. Asset management portal uses separate credentials from corporate SSO. Equipment insurance claims are filed through the IT procurement team.',
   '["get_asset_management_password"]',
   '["reference_engineering_manager_filed_claim", "mention_payout_expires_in_48_hours", "threaten_claim_denial"]',
   'Fake equipment insurance claim targeting Engineering to extract IT asset management credentials',
   '00000000-0000-0000-0000-000000000408')
ON CONFLICT (id) DO NOTHING;

-- Script 4-2: Authority Impersonation × Engineering — Get cloud API keys
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000322', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Cloud Vendor Account Migration — Engineering',
   'Authority Impersonation', 'hard',
   'Target organization runs production infrastructure on AWS with multi-account setup via AWS Organizations. IAM access keys are used for CI/CD pipelines and developer tooling. API keys are rotated quarterly through HashiCorp Vault. Cloud spend is approximately $50K/month. Resource termination protection is enabled on production accounts.',
   '["get_aws_api_access_key"]',
   '["reference_cto_signed_migration_agreement", "threaten_automatic_resource_termination", "cite_midnight_migration_deadline"]',
   'Fake cloud migration targeting Engineering to extract AWS API access keys',
   '00000000-0000-0000-0000-000000000408')
ON CONFLICT (id) DO NOTHING;

-- Script 4-3: Prize/Reward × Engineering — Get GitHub username
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000323', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Developer Conference Prize — Engineering',
   'Prize/Reward', 'easy',
   'Target organization uses GitHub Enterprise for source control with SAML SSO through Okta. Engineers have personal GitHub accounts linked to the org. The team attends AWS re:Invent, KubeCon, and internal hackathons. Conference registrations go through the engineering ops team.',
   '["get_github_username"]',
   '["reference_specific_conference_name", "mention_other_winners_already_claimed", "create_prize_claim_deadline"]',
   'Fake conference raffle targeting Engineering to extract GitHub account information',
   '00000000-0000-0000-0000-000000000408')
ON CONFLICT (id) DO NOTHING;

-- Script 4-4: Technical Support Scam × Engineering — Get VPN password
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000324', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Emergency VPN Credential Reset — Engineering',
   'Technical Support Scam', 'hard',
   'Target organization uses Cisco AnyConnect VPN with Active Directory authentication. VPN access is required for production environment access and internal tools. MFA is enforced via Duo Security push. VPN credentials are separate from SSO for network-layer security. Severity 1 incidents trigger mandatory all-hands response within 30 minutes.',
   '["get_vpn_password"]',
   '["cite_cve_2024_38291", "invoke_ciso_severity_1_declaration", "threaten_permanent_vpn_revocation"]',
   'Fake zero-day VPN emergency targeting Engineering to harvest VPN password',
   '00000000-0000-0000-0000-000000000408')
ON CONFLICT (id) DO NOTHING;

-- Script 4-5: Internal Authority × Engineering — Get personal access token
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000325', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'CTO Code Repository Access — Engineering',
   'Internal Authority', 'hard',
   'Target organization uses GitHub Enterprise with branch protection rules on main. Personal access tokens (PATs) are used for CI/CD integration and API access. Tokens have repo, workflow, and packages scopes. Code reviews require 2 approvals before merge. Repository access is managed through GitHub Teams aligned to engineering squads.',
   '["get_personal_access_token"]',
   '["name_drop_cto", "invoke_board_presentation_tomorrow", "express_cto_frustration_with_it"]',
   'Fake CTO request targeting Engineering to extract a code repository personal access token',
   '00000000-0000-0000-0000-000000000408')
ON CONFLICT (id) DO NOTHING;


-- ═══════════════════════════════════════════════════════════════════════
-- CAMPAIGN 5: Sales Executive Impersonation Test
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO campaigns (id, org_id, created_by, name, description, attack_vector, status) VALUES
  ('00000000-0000-0000-0000-000000000409', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Sales Executive Impersonation Test',
   'Vishing test targeting Sales with executive impersonation, travel fraud, CRM exploits, fake sales awards, and vendor data extraction attacks',
   'Authority Impersonation', 'draft')
ON CONFLICT (id) DO NOTHING;

-- Script 5-1: Financial Scam × Sales — Get employee direct deposit info
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000326', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Commission Payout Verification — Sales',
   'Financial Scam', 'medium',
   'Target organization pays sales commissions monthly through ADP payroll. Commission calculations are tracked in Salesforce CPQ with approval workflows. Direct deposit info is managed through ADP self-service portal. Commission disputes are handled by the sales operations team. Quarterly audits are conducted by external auditors.',
   '["get_direct_deposit_account_number"]',
   '["reference_sales_vp_notification", "threaten_commission_hold_until_next_quarter", "cite_auditor_requirement"]',
   'Fake commission audit targeting Sales to extract direct deposit account number',
   '00000000-0000-0000-0000-000000000409')
ON CONFLICT (id) DO NOTHING;

-- Script 5-2: Authority Impersonation × Sales — Get CRM admin password
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000327', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'CRM Vendor Data Export — Sales',
   'Authority Impersonation', 'hard',
   'Target organization uses Salesforce Enterprise as its CRM with 150+ user licenses. CRM admin access provides full export capabilities for pipeline, customer contacts, and deal data. Authentication is through Okta SSO but admin functions require a separate Salesforce password. Weekly pipeline forecasting meetings rely on live Salesforce dashboards.',
   '["get_crm_admin_password"]',
   '["reference_vp_sales_approved_maintenance", "threaten_pipeline_data_corruption", "cite_forecasting_meeting_tomorrow"]',
   'Fake CRM data issue targeting Sales to extract CRM admin password',
   '00000000-0000-0000-0000-000000000409')
ON CONFLICT (id) DO NOTHING;

-- Script 5-3: Prize/Reward × Sales — Get passport number
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000328', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Sales Achievement Award — Sales',
   'Prize/Reward', 'easy',
   'Target organization runs an annual President''s Club trip for top sales performers. Past destinations include Cancun and Maui. Travel is booked through Concur with Amex corporate cards. Passport info is collected through a secure HR form for international trips. The sales team has 25+ reps across 3 regions.',
   '["get_passport_number"]',
   '["reference_sales_director_nomination", "mention_colleagues_already_registered", "create_registration_deadline"]',
   'Fake President''s Club award targeting Sales to extract passport number',
   '00000000-0000-0000-0000-000000000409')
ON CONFLICT (id) DO NOTHING;

-- Script 5-4: Technical Support Scam × Sales — Get Salesforce password
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000329', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'Salesforce Security Patch — Sales',
   'Technical Support Scam', 'medium',
   'Target organization uses Salesforce Enterprise with Shield Platform Encryption for sensitive fields. Customer PII (contacts, billing info, contracts) is stored in Salesforce. Security patches are managed by the Salesforce admin team. Breach notification is required under CCPA for California customer data. Salesforce sessions timeout after 2 hours of inactivity.',
   '["get_salesforce_password"]',
   '["cite_security_advisory_sa_2024_0847", "threaten_customer_data_breach_notification", "invoke_compliance_team_involvement"]',
   'Fake Salesforce vulnerability targeting Sales to harvest Salesforce password',
   '00000000-0000-0000-0000-000000000409')
ON CONFLICT (id) DO NOTHING;

-- Script 5-5: Internal Authority × Sales — Authorize wire transfer
INSERT INTO scripts (id, org_id, created_by, name, attack_type, difficulty, system_prompt, objectives, escalation_steps, description, campaign_id) VALUES
  ('00000000-0000-0000-0000-000000000330', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010',
   'VP Sales Travel Authorization — Sales',
   'Internal Authority', 'hard',
   'Target organization uses Concur for travel and expense management. Travel authorizations over $5,000 require VP approval through Concur workflow. Emergency travel can be booked with post-trip approval. Corporate Amex cards have a $10,000 single-transaction limit. Wire transfers for client entertainment go through accounts payable.',
   '["authorize_wire_transfer"]',
   '["name_drop_vp_sales_repeatedly", "mention_client_dinner_tonight", "imply_insubordination_will_be_reported"]',
   'Fake VP travel emergency targeting Sales to authorize a fraudulent wire transfer',
   '00000000-0000-0000-0000-000000000409')
ON CONFLICT (id) DO NOTHING;
