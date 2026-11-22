-- Vaani row-level security + Realtime. Contract: docs/CONTRACTS.md §1 "Row-level security".
-- Run after schema.sql. Idempotent. Guarded so it also runs on plain Postgres (tests),
-- where the Supabase roles and the supabase_realtime publication don't exist.
--
-- Model: the browser (anon / authenticated) can only SELECT; every write goes through the
-- FastAPI backend with the service role, which bypasses RLS.

do $$
declare
  t text;
  public_tables text[] := array[
    'areas', 'restaurants', 'restaurant_tables', 'restaurant_slots',
    'hospitals', 'doctors', 'doctor_slots', 'speciality_map',
    'bookings', 'payments', 'calls', 'call_events'];
  has_roles boolean := exists (select 1 from pg_roles where rolname = 'anon')
                   and exists (select 1 from pg_roles where rolname = 'authenticated');
begin
  foreach t in array public_tables loop
    execute format('alter table public.%I enable row level security', t);

    if has_roles then
      execute format('revoke all on table public.%I from anon, authenticated', t);
      execute format('drop policy if exists "read only for everyone" on public.%I', t);
      execute format(
        'create policy "read only for everyone" on public.%I for select to anon, authenticated using (true)', t);
    end if;
  end loop;

  if has_roles then
    -- Whole-table read for the catalogue, slots, payments and live call events.
    grant select on public.areas, public.restaurants, public.restaurant_tables,
                    public.restaurant_slots, public.hospitals, public.doctors,
                    public.doctor_slots, public.speciality_map, public.payments,
                    public.call_events
      to anon, authenticated;

    -- Column-level grants keep phone numbers server-side. Realtime strips columns the
    -- subscriber can't select, so live updates never leak them either.
    grant select (booking_id, service, business_id, doctor_id, date, time, party_size, table_id,
                  name, language, source, status, amount_due_inr, call_id, created_at, updated_at)
      on public.bookings to anon, authenticated;
    grant select (call_id, channel, direction, started_at, ended_at, language, services_used,
                  transcript, outcome_json, tool_timeline, latency_json, recording_url, summary)
      on public.calls to anon, authenticated;

    -- The booking functions are only for the backend.
    revoke execute on function public.book_table(text, date, time, integer, text, text, text, text, text)
      from public, anon, authenticated;
    revoke execute on function public.book_appointment(text, date, time, text, text, text, text, text)
      from public, anon, authenticated;
    revoke execute on function public.cancel_booking(text) from public, anon, authenticated;
  end if;
end $$;

-- Realtime: tables the websites subscribe to (CONTRACTS.md §1).
do $$
declare
  t text;
begin
  if not exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    raise notice 'supabase_realtime publication not found (plain Postgres?) — skipping Realtime setup';
    return;
  end if;
  foreach t in array array['bookings', 'restaurant_slots', 'doctor_slots', 'payments', 'calls', 'call_events'] loop
    if not exists (select 1 from pg_publication_tables
                    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = t) then
      execute format('alter publication supabase_realtime add table public.%I', t);
    end if;
  end loop;
end $$;
