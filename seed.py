import sqlite3
from datetime import datetime

def seed_database():
    # Connect directly to your official database file
    conn = sqlite3.connect('philhealth.db')
    cursor = conn.cursor()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        print("Seeding 10 records into registrant_details (with Spouses)...")
        # Column order matches your exact 20-column schema tuple perfectly
        registrants = [
            ('12-345678900-1', 'DELA CRUZ, JUAN, M.', 'SANTOS, MARIA, P.', 'DELA CRUZ, ANNA, S.', '1990-05-15', 'MANILA', 'Male', 'Married', 'Filipino', None, None, 'Unit 1 Bldg, Manila', 'Unit 1 Bldg, Manila', None, '+63-912-345-6701', None, 'juan.delacruz@email.com', None, 'D-01', now),
            ('12-345678900-2', 'SANTOS, MARIA, P.', 'REYES, ANA, B.', None, '1985-08-22', 'QUEZON CITY', 'Female', 'Single', 'Filipino', None, None, '123 Rizal St, QC', '123 Rizal St, QC', None, '+63-912-345-6702', None, 'maria.santos@email.com', None, 'I-01', now),
            ('12-345678900-3', 'REYES, CARLOS, D.', 'GARCIA, ELENA, F.', 'REYES, LIZA, G.', '1978-11-03', 'MAKATI', 'Male', 'Married', 'Filipino', None, None, '45 Ayala Ave, Makati', '45 Ayala Ave, Makati', None, '+63-912-345-6703', None, 'carlos.reyes@email.com', None, 'D-02', now),
            ('12-345678900-4', 'GARCIA, ELENA, F.', 'MENDOZA, ROSA, H.', 'GARCIA, MARCO, A.', '1995-02-14', 'CEBU CITY', 'Female', 'Married', 'Filipino', None, None, '88 Mango Ave, Cebu', '88 Mango Ave, Cebu', None, '+63-912-345-6704', None, 'elena.garcia@email.com', None, 'D-01', now),
            ('12-345678900-5', 'MENDOZA, ANTONIO, V.', 'CRUZ, CARMEN, B.', 'MENDOZA, JUANA, R.', '1982-07-30', 'DAVAO CITY', 'Male', 'Married', 'Filipino', None, None, '99 Roxas Ave, Davao', '99 Roxas Ave, Davao', None, '+63-912-345-6705', None, 'antonio.mendoza@email.com', None, 'D-01', now),
            ('12-345678900-6', 'BAUTISTA, CARMEN, B.', 'VILLANUEVA, LUZ, T.', None, '2000-12-10', 'PASIG', 'Female', 'Single', 'Filipino', None, None, '77 Ortigas Center, Pasig', '77 Ortigas Center, Pasig', None, '+63-912-345-6706', None, 'carmen.bautista@email.com', None, 'D-02', now),
            ('12-345678900-7', 'VILLANUEVA, RICARDO, E.', 'AQUINO, MARIA, C.', 'VILLANUEVA, MARIA, T.', '1970-04-25', 'CALOOCAN', 'Male', 'Married', 'Filipino', None, None, '33 Edsa, Caloocan', '33 Edsa, Caloocan', None, '+63-912-345-6707', None, 'ricardo.v@email.com', None, 'I-01', now),
            ('12-345678900-8', 'AQUINO, ROSA, H.', 'DELA ROSA, ANA, M.', None, '1992-09-18', 'TAGUIG', 'Female', 'Annulled', 'Filipino', None, None, '22 BGC, Taguig', '22 BGC, Taguig', None, '+63-912-345-6708', None, 'rosa.aquino@email.com', None, 'D-01', now),
            ('12-345678900-9', 'CRUZ, MANUEL, G.', 'FERNANDEZ, LUZ, P.', 'CRUZ, FLORENCE, F.', '1988-03-05', 'PASAY', 'Male', 'Married', 'Filipino', None, None, '11 Taft Ave, Pasay', '11 Taft Ave, Pasay', None, '+63-912-345-6709', None, 'manuel.cruz@email.com', None, 'D-02', now),
            ('12-345678901-0', 'FERNANDEZ, LUZ, P.', 'GOMEZ, MARIA, S.', None, '1998-06-20', 'MANDALUYONG', 'Female', 'Single', 'Dual Citizen', None, None, '55 Shaw Blvd, Mandaluyong', '55 Shaw Blvd, Mandaluyong', None, '+63-912-345-6710', None, 'luz.fernandez@email.com', None, 'I-01', now)
        ]

        cursor.executemany('''
            INSERT OR IGNORE INTO registrant_details (
                PIN, MemberName, MotherMaidenName, SpouseName, BirthDate, BirthPlace, 
                Sex, CivilStatus, Citizenship, PhilSysID, TIN, PermanentAddress, MailingAddress, 
                HomePhone, MobilePhone, BusinessLine, EmailAddress, MemberPasswordHash, MemberTypeID, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', registrants)

        print("Seeding records into dependent_details (with corresponding Spouses)...")
        dependents = [
            # Member 1 (Juan) -> Has Spouse Anna listed as a core profile parameter AND as a dependent row
            ('12-345678900-1', 'DELA CRUZ, ANNA, S.', 'Spouse', '1992-02-14', 'Filipino', 'No', now),
            ('12-345678900-1', 'DELA CRUZ, PEDRO, S.', 'Child', '2015-08-20', 'Filipino', 'No', now),
            ('12-345678900-1', 'DELA CRUZ, SANTIAGO, S.', 'Child', '2018-11-02', 'Filipino', 'No', now),
            
            # Member 3 (Carlos) -> Has Spouse Liza listed as core profile parameter AND as a dependent row
            ('12-345678900-3', 'REYES, LIZA, G.', 'Spouse', '1980-05-25', 'Filipino', 'No', now),
            
            # Member 4 (Elena) -> Has a Spouse column filled, but choosing to claim only her children as dependents
            ('12-345678900-4', 'GARCIA, MIGUEL, M.', 'Child', '2019-07-11', 'Filipino', 'No', now),
            ('12-345678900-4', 'GARCIA, KATERINA, M.', 'Child', '2022-01-30', 'Filipino', 'No', now),
            
            # Member 5 (Antonio) -> Has Spouse Juana listed as core profile parameter AND as a dependent row
            ('12-345678900-5', 'MENDOZA, JUANA, R.', 'Spouse', '1984-09-05', 'Filipino', 'No', now),
            ('12-345678900-5', 'MENDOZA, CLARA, C.', 'Child', '2020-04-12', 'Filipino', 'No', now),
            ('12-345678900-5', 'MENDOZA, ANDRES, C.', 'Child', '2016-06-18', 'Filipino', 'No', now),
            ('12-345678900-5', 'MENDOZA, RAMON, V.', 'Parent', '1951-12-25', 'Filipino', 'Yes', now),
            
            # Member 7 (Ricardo) -> Has a Spouse column filled, but choosing to claim only his elderly parent as a dependent
            ('12-345678900-7', 'VILLANUEVA, JOSE, A.', 'Parent', '1945-01-10', 'Filipino', 'Yes', now),
            
            # Member 9 (Manuel) -> Has a Spouse column filled, but choosing to claim only his children as dependents
            ('12-345678900-9', 'CRUZ, ANGELO, F.', 'Child', '2012-03-14', 'Filipino', 'No', now),
            ('12-345678900-9', 'CRUZ, BEATRICE, F.', 'Child', '2015-10-22', 'Filipino', 'No', now)
        ]

        cursor.executemany('''
            INSERT OR IGNORE INTO dependent_details (
                PIN, DependentName, Relationship, DependentBirthDate, 
                DependentCitizenship, DependentPWD, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', dependents)

        conn.commit()
        print("Success! Database populated cleanly with Spouses aligned across all relevant fields.")

    except sqlite3.Error as e:
        print(f"Database error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    seed_database()