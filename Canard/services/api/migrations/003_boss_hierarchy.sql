-- boss_id index + recursive subordinate lookup RPC + hierarchy seed

-- Index for hierarchy traversals
create index if not exists idx_employees_boss_id on employees(boss_id);

-- Recursive function: returns all subordinates (direct + transitive) of a manager
create or replace function get_subordinates(manager_uuid uuid)
returns table(
    id uuid,
    full_name text,
    email text,
    department text,
    job_title text,
    risk_level text,
    boss_id uuid,
    depth int
) language sql stable as $$
    with recursive tree as (
        select e.id, e.full_name, e.email, e.department, e.job_title,
               e.risk_level, e.boss_id, 1 as depth
        from employees e
        where e.boss_id = manager_uuid
      union all
        select e.id, e.full_name, e.email, e.department, e.job_title,
               e.risk_level, e.boss_id, t.depth + 1
        from employees e
        join tree t on e.boss_id = t.id
    )
    select * from tree;
$$;

-- Seed hierarchy: Lisa Anderson (Marketing Director) is the top manager
-- Sarah Johnson (Finance) and Michael Chen (HR) report to Lisa
-- Emily Rodriguez (Sales) and David Kim (Engineering) report to Sarah
update employees
set boss_id = '00000000-0000-0000-0000-000000000105'
where id in (
    '00000000-0000-0000-0000-000000000101',  -- Sarah Johnson -> Lisa
    '00000000-0000-0000-0000-000000000102'   -- Michael Chen -> Lisa
);

update employees
set boss_id = '00000000-0000-0000-0000-000000000101'
where id in (
    '00000000-0000-0000-0000-000000000103',  -- Emily Rodriguez -> Sarah
    '00000000-0000-0000-0000-000000000104'   -- David Kim -> Sarah
);
