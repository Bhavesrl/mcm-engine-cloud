-- Esegui questo script su Supabase: Dashboard → SQL Editor
-- Abilita la lettura anonima per la React app (anon key)

ALTER TABLE comportamento_hcp   ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_channel ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_read_comportamento_hcp"
  ON comportamento_hcp FOR SELECT TO anon USING (true);

CREATE POLICY "anon_read_performance_channel"
  ON performance_channel FOR SELECT TO anon USING (true);
