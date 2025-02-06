import pdfplumber
import mysql.connector
import re

# MySQL Connection Setup
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Gagan@1910",
        database="mydb"
    )
    cursor = db.cursor()
    print("Database connection successful.")
except mysql.connector.Error as err:
    print(f"Error: {err}")
    exit()

pdf_path = r"C:\Users\J GAGAN CHANDRA\OneDrive\Desktop\Result of II BTech I Semester (R20R19R16) Regular_241014_114249.pdf"

# Extract and Process PDF Data
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            lines = text.split("\n")
            for line in lines:
                parts = line.split()

                if len(parts) < 5:  # Ignore lines that are too short
                    continue

                htno = parts[0]
                academic_year = htno[:2]  # Extract first two digits as academic year
                branch = "Unknown"
                if htno[6:8] == "05":
                    branch = "CSE"
                elif htno[6:8] == "04":
                    branch = "ECE"
                elif htno[6:8] == "02":
                    branch = "MECH"
                elif htno[6:8] == "03":
                    branch = "EEE"
                elif htno[6:8] == "42":
                    branch = "CSM"

                subcode = parts[1]

                # Extract subject name dynamically
                subname_parts = []
                for part in parts[2:]:
                    if re.search(r'\d', part):  # Stop when encountering a number
                        break
                    subname_parts.append(part)

                subname = " ".join(subname_parts)

                # Extract internals, grade, and credits dynamically
                try:
                    num_parts = [p for p in parts if re.match(r'^\d+(\.\d+)?$', p) or re.match(r'^[A-Za-z\+]+$', p)]

                    if len(num_parts) < 3:
                        print(f"Skipping invalid line: {parts}")
                        continue

                    internals = int(num_parts[-3])  # Last 3rd item should be internals
                    grade = num_parts[-2].strip()  # Last 2nd item should be grade
                    credits = float(num_parts[-1])  # Last item should be credits

                except (ValueError, IndexError):
                    print(f"Skipping invalid line: {parts}")
                    continue

                # Print the extracted values
                print(f"Htno: {htno}, Subcode: {subcode}, Subname: {subname}, Internals: {internals}, Grade: {grade}, Credits: {credits}")

                # Generate academic_id and academic_year range
                year = int("20" + academic_year)  # Convert to full year format (e.g., 22 -> 2022)
                end_year = year + 4  # Add 4 years to form the academic year range
                academic_year_range = f"{year}-{end_year}"
                academic_id = int(academic_year)

                # Insert or update data in AcademicYear table
                cursor.execute("""
                    INSERT INTO AcademicYear (academic_id, academic_year)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE academic_year = VALUES(academic_year)
                """, (academic_id, academic_year_range))

                # Insert or update data into year_table with year_code (Handling duplicates)
                for i in range(4):  # Generate data for 4 years
                    year_entry = year + i
                    year_code = f"{academic_id}{i + 1}{branch}"  # Generate year_code dynamically

                    cursor.execute("""
                        INSERT INTO year_table (academic_id, year, branch, year_code)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE year = VALUES(year), branch = VALUES(branch), year_code = VALUES(year_code)
                    """, (academic_id, year_entry, branch, year_code))

 
                    

                if grade == "F" or grade == "ABSENT":
                    print(f"Skipping grade {grade} for student {htno}")
+                    continue
                else:
                    # Insert Data into sub_table (sub_code, sub_name, and credits)
                    cursor.execute("""
                        INSERT INTO sub_table (sub_code, sub_name, credits)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE sub_name = VALUES(sub_name), credits = VALUES(credits)
                    """, (subcode, subname, credits))


                sem_id = subcode[3:5]
                # Assuming you have sem_id and sub_code extracted
                try:
                    cursor.execute("""
                        INSERT INTO semsub_table (sem_id, sub_code)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE sub_code = VALUES(sub_code);
                    """, (sem_id, subcode))
                except mysql.connector.Error as err:
                    print(f"Error inserting into semsub_table: {err}")

                

                # Insert or update data in student_table
                cursor.execute("""
                    INSERT INTO student_table (student_regno, academic_id, branch)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE academic_id = VALUES(academic_id), branch = VALUES(branch)
                """, (htno, academic_id, branch))

                # Insert data into result_table
                cursor.execute("""
                    INSERT INTO result_table (student_regno, sub_code, result_grade, internals)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE result_grade = VALUES(result_grade), internals = VALUES(internals)
                """, (htno, subcode, grade, internals))

                # Insert into year_sem by joining year_table and sem_table (Handle duplicates)
                for i in range(4):  # Generate data for 4 years
                    year_entry = year + i
                    year_code = f"{academic_id}{i + 1}{branch}"
                   
                    if(year_code[2] != sem_id[0]):
                        continue
                    else :
                      
                        cursor.execute("""
                            INSERT INTO year_sem (year_code, sem_id)
                            VALUES (%s, %s)
                            ON DUPLICATE KEY UPDATE sem_id = VALUES(sem_id);

                            """,(year_code,sem_id))
db.commit()

# Close the connection
cursor.close()
db.close()
