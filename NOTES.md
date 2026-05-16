# Notes
Mga note and other stuff that may be important, of whatnot.

#### To populate data in `philhealth.db` -- membership_details table
First, on terminal...
```sql
sqlite3 philhealth.db
```

then,
```sql
INSERT INTO membership_details (MemberTypeID, MemberType) VALUES
('D-01', 'Employed Private'),
('D-02', 'Employed Government'),
('D-03', 'Professional Practitioner'),
('D-04', 'Self-Earning Individual'),
('D-05', 'Kasambahay'),
('D-06', 'Family Driver'),
('D-07', 'Migrant Worker'),
('D-08', 'Lifetime Member'),
('D-09', 'Filipinos with Dual Citizenship/Living Abroad'),
('D-10', 'Foreign National'),
('I-01', 'Listahanang'),
('I-02', '4Ps/MCCT'),
('I-03', 'Senior Citizen'),
('I-04', 'PAMANA'),
('I-05', 'KIA/KIPO'),
('I-06', 'Bangsamoro/Normalization'),
('I-07', 'LGU-sponsored'),
('I-08', 'NGA-sponsored'),
('I-09', 'Private-sponsored'),
('I-10', 'Person with Disability');
```

#### To make the membership_details table un-editable
On terminal,
```sql
-- Prevent Updates
CREATE TRIGGER stop_update_membership
BEFORE UPDATE ON membership_details
BEGIN
  SELECT RAISE(ABORT, 'This table is read-only and cannot be updated.');
END;

-- Prevent Deletions
CREATE TRIGGER stop_delete_membership
BEFORE DELETE ON membership_details
BEGIN
  SELECT RAISE(ABORT, 'This table is read-only and cannot be deleted.');
END;
```