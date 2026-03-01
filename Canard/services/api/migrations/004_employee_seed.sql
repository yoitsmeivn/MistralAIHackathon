-- 004_employee_seed.sql
-- Expand org chart to ~40 employees across 7 departments with 5-level hierarchy
-- Preserves existing 5 employee UUIDs (101-105) so call/campaign data stays valid

-- ══════════════════════════════════════════════════════════════════════
-- PASS 1: Update existing employees with new titles to fit bigger org
-- ══════════════════════════════════════════════════════════════════════

-- 101 Sarah Johnson: Financial Analyst → Controller (Finance)
UPDATE employees SET job_title = 'Controller', department = 'Finance'
WHERE id = '00000000-0000-0000-0000-000000000101';

-- 102 Michael Chen: HR Manager → VP People (People)
UPDATE employees SET job_title = 'VP People', department = 'People'
WHERE id = '00000000-0000-0000-0000-000000000102';

-- 103 Emily Rodriguez: Sales Representative → Sales Ops Manager (Sales)
UPDATE employees SET job_title = 'Sales Ops Manager', department = 'Sales'
WHERE id = '00000000-0000-0000-0000-000000000103';

-- 104 David Kim: Software Engineer → People Ops Analyst (People)
UPDATE employees SET job_title = 'People Ops Analyst', department = 'People'
WHERE id = '00000000-0000-0000-0000-000000000104';

-- 105 Lisa Anderson: Marketing Director → VP Marketing (Marketing)
UPDATE employees SET job_title = 'VP Marketing', department = 'Marketing'
WHERE id = '00000000-0000-0000-0000-000000000105';

-- ══════════════════════════════════════════════════════════════════════
-- PASS 2: Insert ~33 new employees
-- ══════════════════════════════════════════════════════════════════════

INSERT INTO employees (id, org_id, full_name, email, phone, department, job_title, risk_level) VALUES
  -- CEO
  ('00000000-0000-0000-0000-000000000106', '00000000-0000-0000-0000-000000000001',
   'Rachel Torres', 'rachel.torres@acme-corp.com', '+15556001001', 'Executive', 'CEO', 'unknown'),

  -- VP Engineering
  ('00000000-0000-0000-0000-000000000107', '00000000-0000-0000-0000-000000000001',
   'James Park', 'james.park@acme-corp.com', '+15556001002', 'Engineering', 'VP Engineering', 'unknown'),

  -- VP Finance
  ('00000000-0000-0000-0000-000000000108', '00000000-0000-0000-0000-000000000001',
   'William Chang', 'william.chang@acme-corp.com', '+15556001003', 'Finance', 'VP Finance', 'unknown'),

  -- VP Sales
  ('00000000-0000-0000-0000-000000000109', '00000000-0000-0000-0000-000000000001',
   'Diana Mercer', 'diana.mercer@acme-corp.com', '+15556001004', 'Sales', 'VP Sales', 'unknown'),

  -- Head of Security
  ('00000000-0000-0000-0000-000000000110', '00000000-0000-0000-0000-000000000001',
   'Nathaniel Cross', 'nathaniel.cross@acme-corp.com', '+15556001005', 'Security', 'Head of Security', 'unknown'),

  -- General Counsel
  ('00000000-0000-0000-0000-000000000111', '00000000-0000-0000-0000-000000000001',
   'Patricia Whitfield', 'patricia.whitfield@acme-corp.com', '+15556001006', 'Legal', 'General Counsel', 'unknown'),

  -- Sr. Engineering Manager (under James Park)
  ('00000000-0000-0000-0000-000000000112', '00000000-0000-0000-0000-000000000001',
   'Anika Patel', 'anika.patel@acme-corp.com', '+15556001007', 'Engineering', 'Sr. Engineering Manager', 'unknown'),

  -- Engineering Manager (under James Park)
  ('00000000-0000-0000-0000-000000000113', '00000000-0000-0000-0000-000000000001',
   'Ben Hawkins', 'ben.hawkins@acme-corp.com', '+15556001008', 'Engineering', 'Engineering Manager', 'unknown'),

  -- Financial Analyst (under William Chang)
  ('00000000-0000-0000-0000-000000000114', '00000000-0000-0000-0000-000000000001',
   'Nina Kowalski', 'nina.kowalski@acme-corp.com', '+15556001009', 'Finance', 'Financial Analyst', 'unknown'),

  -- Revenue Analyst (under William Chang)
  ('00000000-0000-0000-0000-000000000115', '00000000-0000-0000-0000-000000000001',
   'Alex Reeves', 'alex.reeves@acme-corp.com', '+15556001010', 'Finance', 'Revenue Analyst', 'unknown'),

  -- Sales Director (under Diana Mercer)
  ('00000000-0000-0000-0000-000000000116', '00000000-0000-0000-0000-000000000001',
   'Kevin O''Brien', 'kevin.obrien@acme-corp.com', '+15556001011', 'Sales', 'Sales Director', 'unknown'),

  -- Content Lead (under Lisa Anderson / VP Marketing)
  ('00000000-0000-0000-0000-000000000117', '00000000-0000-0000-0000-000000000001',
   'Samantha Price', 'samantha.price@acme-corp.com', '+15556001012', 'Marketing', 'Content Lead', 'unknown'),

  -- Growth Manager (under Lisa Anderson / VP Marketing)
  ('00000000-0000-0000-0000-000000000118', '00000000-0000-0000-0000-000000000001',
   'Ian Gallagher', 'ian.gallagher@acme-corp.com', '+15556001013', 'Marketing', 'Growth Manager', 'unknown'),

  -- Marketing Coordinator (under Lisa Anderson / VP Marketing)
  ('00000000-0000-0000-0000-000000000119', '00000000-0000-0000-0000-000000000001',
   'Ava Chen', 'ava.chen@acme-corp.com', '+15556001014', 'Marketing', 'Marketing Coordinator', 'unknown'),

  -- HR Manager (under Michael Chen / VP People)
  ('00000000-0000-0000-0000-000000000120', '00000000-0000-0000-0000-000000000001',
   'Tanya Brooks', 'tanya.brooks@acme-corp.com', '+15556001015', 'People', 'HR Manager', 'unknown'),

  -- Security Engineer (under Nathaniel Cross)
  ('00000000-0000-0000-0000-000000000121', '00000000-0000-0000-0000-000000000001',
   'Fatima Al-Rashid', 'fatima.alrashid@acme-corp.com', '+15556001016', 'Security', 'Security Engineer', 'unknown'),

  -- Compliance Analyst (under Nathaniel Cross)
  ('00000000-0000-0000-0000-000000000122', '00000000-0000-0000-0000-000000000001',
   'Greg Morales', 'greg.morales@acme-corp.com', '+15556001017', 'Security', 'Compliance Analyst', 'unknown'),

  -- Paralegal (under Patricia Whitfield)
  ('00000000-0000-0000-0000-000000000123', '00000000-0000-0000-0000-000000000001',
   'Ryan Cho', 'ryan.cho@acme-corp.com', '+15556001018', 'Legal', 'Paralegal', 'unknown'),

  -- Staff Engineer (under Anika Patel)
  ('00000000-0000-0000-0000-000000000124', '00000000-0000-0000-0000-000000000001',
   'Marcus Webb', 'marcus.webb@acme-corp.com', '+15556001019', 'Engineering', 'Staff Engineer', 'unknown'),

  -- Senior Engineer (under Anika Patel)
  ('00000000-0000-0000-0000-000000000125', '00000000-0000-0000-0000-000000000001',
   'Priya Krishnamurthy', 'priya.krishnamurthy@acme-corp.com', '+15556001020', 'Engineering', 'Senior Engineer', 'unknown'),

  -- Software Engineer (under Anika Patel)
  ('00000000-0000-0000-0000-000000000126', '00000000-0000-0000-0000-000000000001',
   'Tyler Nguyen', 'tyler.nguyen@acme-corp.com', '+15556001021', 'Engineering', 'Software Engineer', 'unknown'),

  -- Software Engineer (under Anika Patel)
  ('00000000-0000-0000-0000-000000000127', '00000000-0000-0000-0000-000000000001',
   'Jasmine Okafor', 'jasmine.okafor@acme-corp.com', '+15556001022', 'Engineering', 'Software Engineer', 'unknown'),

  -- Senior Engineer (under Ben Hawkins)
  ('00000000-0000-0000-0000-000000000128', '00000000-0000-0000-0000-000000000001',
   'Claire Dubois', 'claire.dubois@acme-corp.com', '+15556001023', 'Engineering', 'Senior Engineer', 'unknown'),

  -- Software Engineer (under Ben Hawkins)
  ('00000000-0000-0000-0000-000000000129', '00000000-0000-0000-0000-000000000001',
   'Ravi Mehta', 'ravi.mehta@acme-corp.com', '+15556001024', 'Engineering', 'Software Engineer', 'unknown'),

  -- Junior Engineer (under Ben Hawkins)
  ('00000000-0000-0000-0000-000000000130', '00000000-0000-0000-0000-000000000001',
   'Sophie Andersson', 'sophie.andersson@acme-corp.com', '+15556001025', 'Engineering', 'Junior Engineer', 'unknown'),

  -- Senior Accountant (under Sarah Johnson / Controller)
  ('00000000-0000-0000-0000-000000000131', '00000000-0000-0000-0000-000000000001',
   'Derek Lawson', 'derek.lawson@acme-corp.com', '+15556001026', 'Finance', 'Senior Accountant', 'unknown'),

  -- Staff Accountant (under Sarah Johnson / Controller)
  ('00000000-0000-0000-0000-000000000132', '00000000-0000-0000-0000-000000000001',
   'Maria Santos', 'maria.santos@acme-corp.com', '+15556001027', 'Finance', 'Staff Accountant', 'unknown'),

  -- Account Executive (under Kevin O'Brien)
  ('00000000-0000-0000-0000-000000000133', '00000000-0000-0000-0000-000000000001',
   'Zoe Hartman', 'zoe.hartman@acme-corp.com', '+15556001028', 'Sales', 'Account Executive', 'unknown'),

  -- Account Executive (under Kevin O'Brien)
  ('00000000-0000-0000-0000-000000000134', '00000000-0000-0000-0000-000000000001',
   'Omar Farouk', 'omar.farouk@acme-corp.com', '+15556001029', 'Sales', 'Account Executive', 'unknown'),

  -- SDR (under Kevin O'Brien)
  ('00000000-0000-0000-0000-000000000135', '00000000-0000-0000-0000-000000000001',
   'Lily Tanaka', 'lily.tanaka@acme-corp.com', '+15556001030', 'Sales', 'SDR', 'unknown'),

  -- Sales Ops Analyst (under Emily Rodriguez / Sales Ops Manager)
  ('00000000-0000-0000-0000-000000000136', '00000000-0000-0000-0000-000000000001',
   'Jordan Castillo', 'jordan.castillo@acme-corp.com', '+15556001031', 'Sales', 'Sales Ops Analyst', 'unknown'),

  -- HR Specialist (under Tanya Brooks)
  ('00000000-0000-0000-0000-000000000137', '00000000-0000-0000-0000-000000000001',
   'Cody Simmons', 'cody.simmons@acme-corp.com', '+15556001032', 'People', 'HR Specialist', 'unknown'),

  -- Recruiter (under Tanya Brooks)
  ('00000000-0000-0000-0000-000000000138', '00000000-0000-0000-0000-000000000001',
   'Hannah Johansson', 'hannah.johansson@acme-corp.com', '+15556001033', 'People', 'Recruiter', 'unknown')

ON CONFLICT (id) DO NOTHING;

-- ══════════════════════════════════════════════════════════════════════
-- PASS 3: Set boss_id hierarchy
-- Reset existing boss_id first, then set new hierarchy top-down
-- ══════════════════════════════════════════════════════════════════════

-- Clear old hierarchy for existing employees
UPDATE employees SET boss_id = NULL
WHERE org_id = '00000000-0000-0000-0000-000000000001';

-- Level 2: VPs / Heads report to CEO (Rachel Torres = 106)
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000106'
WHERE id IN (
    '00000000-0000-0000-0000-000000000107',  -- James Park (VP Engineering)
    '00000000-0000-0000-0000-000000000108',  -- William Chang (VP Finance)
    '00000000-0000-0000-0000-000000000109',  -- Diana Mercer (VP Sales)
    '00000000-0000-0000-0000-000000000105',  -- Lisa Anderson (VP Marketing) ★
    '00000000-0000-0000-0000-000000000102',  -- Michael Chen (VP People) ★
    '00000000-0000-0000-0000-000000000110',  -- Nathaniel Cross (Head of Security)
    '00000000-0000-0000-0000-000000000111'   -- Patricia Whitfield (General Counsel)
);

-- Level 3: Engineering managers report to VP Engineering (James Park = 107)
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000107'
WHERE id IN (
    '00000000-0000-0000-0000-000000000112',  -- Anika Patel (Sr. Eng Manager)
    '00000000-0000-0000-0000-000000000113'   -- Ben Hawkins (Eng Manager)
);

-- Level 3: Finance reports to VP Finance (William Chang = 108)
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000108'
WHERE id IN (
    '00000000-0000-0000-0000-000000000101',  -- Sarah Johnson (Controller) ★
    '00000000-0000-0000-0000-000000000114',  -- Nina Kowalski (Financial Analyst)
    '00000000-0000-0000-0000-000000000115'   -- Alex Reeves (Revenue Analyst)
);

-- Level 3: Sales managers report to VP Sales (Diana Mercer = 109)
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000109'
WHERE id IN (
    '00000000-0000-0000-0000-000000000116',  -- Kevin O'Brien (Sales Director)
    '00000000-0000-0000-0000-000000000103'   -- Emily Rodriguez (Sales Ops Manager) ★
);

-- Level 3: Marketing reports to VP Marketing (Lisa Anderson = 105) ★
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000105'
WHERE id IN (
    '00000000-0000-0000-0000-000000000117',  -- Samantha Price (Content Lead)
    '00000000-0000-0000-0000-000000000118',  -- Ian Gallagher (Growth Manager)
    '00000000-0000-0000-0000-000000000119'   -- Ava Chen (Marketing Coordinator)
);

-- Level 3: People reports to VP People (Michael Chen = 102) ★
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000102'
WHERE id IN (
    '00000000-0000-0000-0000-000000000120',  -- Tanya Brooks (HR Manager)
    '00000000-0000-0000-0000-000000000104'   -- David Kim (People Ops Analyst) ★
);

-- Level 3: Security reports to Head of Security (Nathaniel Cross = 110)
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000110'
WHERE id IN (
    '00000000-0000-0000-0000-000000000121',  -- Fatima Al-Rashid (Security Engineer)
    '00000000-0000-0000-0000-000000000122'   -- Greg Morales (Compliance Analyst)
);

-- Level 3: Legal reports to General Counsel (Patricia Whitfield = 111)
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000111'
WHERE id = '00000000-0000-0000-0000-000000000123';  -- Ryan Cho (Paralegal)

-- Level 4: Anika Patel's team (Sr. Eng Manager = 112)
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000112'
WHERE id IN (
    '00000000-0000-0000-0000-000000000124',  -- Marcus Webb (Staff Engineer)
    '00000000-0000-0000-0000-000000000125',  -- Priya Krishnamurthy (Senior Engineer)
    '00000000-0000-0000-0000-000000000126',  -- Tyler Nguyen (Software Engineer)
    '00000000-0000-0000-0000-000000000127'   -- Jasmine Okafor (Software Engineer)
);

-- Level 4: Ben Hawkins' team (Eng Manager = 113)
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000113'
WHERE id IN (
    '00000000-0000-0000-0000-000000000128',  -- Claire Dubois (Senior Engineer)
    '00000000-0000-0000-0000-000000000129',  -- Ravi Mehta (Software Engineer)
    '00000000-0000-0000-0000-000000000130'   -- Sophie Andersson (Junior Engineer)
);

-- Level 4: Sarah Johnson's team (Controller = 101) ★
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000101'
WHERE id IN (
    '00000000-0000-0000-0000-000000000131',  -- Derek Lawson (Senior Accountant)
    '00000000-0000-0000-0000-000000000132'   -- Maria Santos (Staff Accountant)
);

-- Level 4: Kevin O'Brien's team (Sales Director = 116)
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000116'
WHERE id IN (
    '00000000-0000-0000-0000-000000000133',  -- Zoe Hartman (Account Executive)
    '00000000-0000-0000-0000-000000000134',  -- Omar Farouk (Account Executive)
    '00000000-0000-0000-0000-000000000135'   -- Lily Tanaka (SDR)
);

-- Level 4: Emily Rodriguez's team (Sales Ops Manager = 103) ★
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000103'
WHERE id = '00000000-0000-0000-0000-000000000136';  -- Jordan Castillo (Sales Ops Analyst)

-- Level 4: Tanya Brooks' team (HR Manager = 120)
UPDATE employees SET boss_id = '00000000-0000-0000-0000-000000000120'
WHERE id IN (
    '00000000-0000-0000-0000-000000000137',  -- Cody Simmons (HR Specialist)
    '00000000-0000-0000-0000-000000000138'   -- Hannah Johansson (Recruiter)
);
