import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

# --- Custom Styles ---
st.markdown("""
    <style>
        .main {
            background-color: #f7f7f7;
            padding: 2rem;
        }
        .stButton > button {
            background-color: #004466;
            color: white;
            font-weight: bold;
        }
        .stTextInput > div > input {
            background-color: #ffffff !important;
        }
        h1, h2, h3 {
            color: #003366;
        }
        .css-1d391kg {  /* sidebar text */
            color: white;
        }
        .block-container {
            padding-top: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Database connection ---
def connect_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Datascience12.',
        database='library'
    )

# --- Sidebar ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2991/2991108.png", width=100)
st.sidebar.markdown("## 📚 Library Management")
st.sidebar.markdown("---")

menu = ["🏠 Home", "📘 Book Management", "📤 Issue Management", "👨‍🎓 Student Management", "📊 Reports"]
choice = st.sidebar.radio("Navigation", menu)

conn = connect_db()
cursor = conn.cursor()

# --- Home ---
if choice == "🏠 Home":
    st.markdown("## 🏫 Welcome to the Library Dashboard")
    st.markdown("---")

    cursor.execute("SELECT COUNT(*) FROM books")
    book_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM students")
    student_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM book_issue WHERE available_status = 1")
    available_books = cursor.fetchone()[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("📚 Total Books", book_count)
    col2.metric("👥 Students", student_count)
    col3.metric("✅ Available Books", available_books)

    st.markdown("---")
    st.success("Use the sidebar to manage library operations.")

# --- Book Management ---
elif choice == "📘 Book Management":
    st.markdown("## 📘 Book Management")
    st.markdown("---")

    search_term = st.text_input("🔍 Search Books (Title/Author)")
    if search_term:
        cursor.execute(
            "SELECT book_id, title, author, category_id FROM books "
            "WHERE title LIKE %s OR author LIKE %s",
            (f'%{search_term}%', f'%{search_term}%')
        )
        books = cursor.fetchall()
        if books:
            st.dataframe(pd.DataFrame(books, columns=["ID", "Title", "Author", "Category ID"]))
        else:
            st.warning("No books found.")

    with st.expander("➕ Add New Book"):
        with st.form("book_form"):
            title = st.text_input("Title")
            author = st.text_input("Author")
            description = st.text_area("Description")
            cursor.execute("SELECT id, category FROM book_categories")
            categories = {cat[1]: cat[0] for cat in cursor.fetchall()}
            category = st.selectbox("Category", options=categories.keys())
            added_by = st.number_input("Added By (User ID)", min_value=1)

            if st.form_submit_button("✅ Add Book"):
                category_id = categories[category]
                cursor.execute(
                    "INSERT INTO books (title, author, description, category_id, added_by) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (title, author, description, category_id, added_by)
                )
                conn.commit()
                st.success("✅ Book added successfully!")

# --- Issue Management ---
elif choice == "📤 Issue Management":
    st.markdown("## 📤 Book Issue & Return")
    st.markdown("---")

    with st.expander("📦 Issue Book"):
        with st.form("issue_form"):
            cursor.execute("SELECT issue_id, book_id FROM book_issue WHERE available_status = 1")
            available_issues = cursor.fetchall()
            issue_options = {f"Book {issue[1]} (Copy {issue[0]})": issue[0] for issue in available_issues}
            issue_id = st.selectbox("Available Copies", options=list(issue_options.values()), format_func=lambda x: list(issue_options.keys())[list(issue_options.values()).index(x)])

            cursor.execute("SELECT student_id, roll_num, CONCAT(first_name, ' ', last_name) FROM students")
            students = cursor.fetchall()
            student_options = {f"{s[1]} - {s[2]}": s[0] for s in students}
            student_id = st.selectbox("Student", options=list(student_options.values()), format_func=lambda x: list(student_options.keys())[list(student_options.values()).index(x)])

            issue_days = st.number_input("Issue Duration (Days)", min_value=1, value=14)
            issued_by = st.number_input("Issued By (User ID)", min_value=1)

            if st.form_submit_button("📤 Issue Book"):
                issue_date = datetime.now()
                return_date = issue_date + timedelta(days=issue_days)

                cursor.execute("UPDATE book_issue SET available_status = 0 WHERE issue_id = %s", (issue_id,))
                cursor.execute("INSERT INTO book_issue_log (book_issue_id, student_id, issue_by, issued_at, return_time) VALUES (%s, %s, %s, %s, %s)",
                               (issue_id, student_id, issued_by, issue_date.strftime('%Y-%m-%d %H:%M:%S'), return_date.strftime('%Y-%m-%d %H:%M:%S')))
                cursor.execute("UPDATE students SET books_issued = books_issued + 1 WHERE student_id = %s", (student_id,))
                conn.commit()
                st.success("✅ Book issued successfully!")

    with st.expander("📥 Return Book"):
        with st.form("return_form"):
            cursor.execute(
                "SELECT l.id, b.title, s.roll_num, s.first_name, s.last_name "
                "FROM book_issue_log l "
                "JOIN book_issue i ON l.book_issue_id = i.issue_id "
                "JOIN books b ON i.book_id = b.book_id "
                "JOIN students s ON l.student_id = s.student_id "
                "WHERE i.available_status = 0"
            )
            issued_books = cursor.fetchall()
            if not issued_books:
                st.warning("No books currently issued.")
            else:
                issue_options = {f"{book[1]} to {book[2]} - {book[3]} {book[4]}": book[0] for book in issued_books}
                log_id = st.selectbox("Issued Books", options=list(issue_options.values()), format_func=lambda x: list(issue_options.keys())[list(issue_options.values()).index(x)])

                if st.form_submit_button("📥 Return Book"):
                    cursor.execute("SELECT book_issue_id, student_id FROM book_issue_log WHERE id = %s", (log_id,))
                    log_entry = cursor.fetchone()
                    cursor.execute("UPDATE book_issue SET available_status = 1 WHERE issue_id = %s", (log_entry[0],))
                    cursor.execute("UPDATE students SET books_issued = books_issued - 1 WHERE student_id = %s", (log_entry[1],))
                    conn.commit()
                    st.success("✅ Book returned successfully!")

# --- Student Management ---
elif choice == "👨‍🎓 Student Management":
    st.markdown("## 👨‍🎓 Student Management")
    st.markdown("---")

    cursor.execute(
        "SELECT s.student_id, s.roll_num, s.first_name, s.last_name, "
        "c.category, b.branch, s.books_issued, "
        "CASE WHEN s.approved = 1 THEN 'Approved' WHEN s.rejected = 1 THEN 'Rejected' ELSE 'Pending' END AS status "
        "FROM students s "
        "JOIN student_categories c ON s.category = c.cat_id "
        "JOIN branches b ON s.branch = b.id"
    )
    students = cursor.fetchall()
    if students:
        st.dataframe(pd.DataFrame(students, columns=["ID", "Roll No", "First Name", "Last Name", "Category", "Branch", "Books Issued", "Status"]))
    else:
        st.info("No students found.")

    with st.expander("➕ Add New Student"):
        with st.form("student_form"):
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            roll_num = st.text_input("Roll Number")
            email = st.text_input("Email")

            cursor.execute("SELECT cat_id, category FROM student_categories")
            categories = {cat[1]: cat[0] for cat in cursor.fetchall()}
            category = st.selectbox("Category", options=categories.keys())

            cursor.execute("SELECT id, branch FROM branches")
            branches = {branch[1]: branch[0] for branch in cursor.fetchall()}
            branch = st.selectbox("Branch", options=branches.keys())

            year = st.number_input("Year", min_value=1900, max_value=2100, value=datetime.now().year)

            if st.form_submit_button("✅ Add Student"):
                category_id = categories[category]
                branch_id = branches[branch]
                cursor.execute(
                    "INSERT INTO students (first_name, last_name, roll_num, email_id, category, branch, year) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (first_name, last_name, roll_num, email, category_id, branch_id, year)
                )
                conn.commit()
                st.success("✅ Student added successfully!")

elif choice == "📊 Reports":
    st.markdown("## 📊 Library Reports with Visuals")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📕 Overdue Books", "⛔ Borrowing Limits", "🧑‍💼 Librarian Performance"])

    # 1. 📕 Overdue Books
    with tab1:
        st.subheader("📕 Overdue Books")
        cursor.execute("""
            SELECT b.title, s.roll_num, CONCAT(s.first_name, ' ', s.last_name) AS student_name,
                   l.issued_at, l.return_time,
                   DATEDIFF(CURDATE(), STR_TO_DATE(l.return_time, '%Y-%m-%d %H:%i:%s')) AS days_overdue
            FROM book_issue_log l
            JOIN book_issue i ON l.book_issue_id = i.issue_id
            JOIN books b ON i.book_id = b.book_id
            JOIN students s ON l.student_id = s.student_id
            WHERE STR_TO_DATE(l.return_time, '%Y-%m-%d %H:%i:%s') < CURDATE()
              AND i.available_status = 0
        """)
        overdue = cursor.fetchall()
        if overdue:
            df = pd.DataFrame(overdue, columns=["Book Title", "Roll No", "Student Name", "Issued At", "Return By", "Days Overdue"])
            st.dataframe(df)

            chart_data = df.groupby("Book Title")["Days Overdue"].sum().reset_index()
            st.bar_chart(chart_data.set_index("Book Title"))
        else:
            st.info("✅ No overdue books found.")

    # 2. ⛔ Borrowing Limits
    with tab2:
        st.subheader("⛔ Borrowing Limits")
        cursor.execute("""
            SELECT c.category, c.max_allowed, COUNT(s.student_id) AS students,
                   SUM(CASE WHEN s.books_issued >= c.max_allowed THEN 1 ELSE 0 END) AS exceeded_limit
            FROM student_categories c
            LEFT JOIN students s ON c.cat_id = s.category
            GROUP BY c.cat_id, c.category, c.max_allowed
        """)
        limits = cursor.fetchall()
        if limits:
            df = pd.DataFrame(limits, columns=["Category", "Max Allowed", "Total Students", "Exceeded Limit"])
            st.dataframe(df)

            st.bar_chart(df.set_index("Category")[["Total Students", "Exceeded Limit"]])
        else:
            st.warning("No borrowing data found.")

    # 3. 🧑‍💼 Librarian Performance
    with tab3:
        st.subheader("🧑‍💼 Librarian Performance")
        cursor.execute("""
            SELECT u.name, COUNT(l.id) AS books_issued,
                   SUM(CASE WHEN i.available_status = 0 THEN 1 ELSE 0 END) AS currently_borrowed
            FROM book_issue_log l
            JOIN users u ON l.issue_by = u.id
            JOIN book_issue i ON l.book_issue_id = i.issue_id
            GROUP BY u.id, u.name
        """)
        performance = cursor.fetchall()
        if performance:
            df = pd.DataFrame(performance, columns=["Librarian", "Total Issued", "Currently Borrowed"])
            st.dataframe(df)

            st.bar_chart(df.set_index("Librarian")[["Total Issued", "Currently Borrowed"]])
        else:
            st.warning("No librarian issue data yet.")


# --- Close connections ---
cursor.close()
conn.close()
