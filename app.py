import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

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

# --- Database Setup ---
def init_db():
    """Initialize SQLite database and create tables with sample data"""
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Create tables if not exists
    c.execute("""
    CREATE TABLE IF NOT EXISTS book_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        description TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        added_by INTEGER NOT NULL,
        added_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS book_issue (
        issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        available_status INTEGER NOT NULL DEFAULT 1,
        added_by INTEGER NOT NULL,
        added_at_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS book_issue_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_issue_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        issue_by INTEGER NOT NULL,
        issued_at TIMESTAMP NOT NULL,
        return_time TIMESTAMP NOT NULL,
        time_stamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_num TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email_id TEXT,
        category INTEGER,
        branch INTEGER,
        year INTEGER,
        books_issued INTEGER DEFAULT 0,
        approved INTEGER DEFAULT 0,
        rejected INTEGER DEFAULT 0
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS student_categories (
        cat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        max_allowed INTEGER DEFAULT 5
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch TEXT NOT NULL
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    """)
    
    # Insert sample data if tables are empty
    c.execute("SELECT COUNT(*) FROM book_categories")
    if c.fetchone()[0] == 0:
        categories = [('Fiction',), ('Non-Fiction',), ('Science',), ('History',)]
        c.executemany("INSERT INTO book_categories (category) VALUES (?)", categories)
    
    c.execute("SELECT COUNT(*) FROM student_categories")
    if c.fetchone()[0] == 0:
        student_cats = [('Undergraduate', 5), ('Graduate', 7), ('Faculty', 10)]
        c.executemany("INSERT INTO student_categories (category, max_allowed) VALUES (?, ?)", student_cats)
    
    c.execute("SELECT COUNT(*) FROM branches")
    if c.fetchone()[0] == 0:
        branches = [('Computer Science',), ('Electrical',), ('Mechanical',), ('Civil',)]
        c.executemany("INSERT INTO branches (branch) VALUES (?)", branches)
    
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        users = [('Admin User',), ('Librarian 1',), ('Librarian 2',)]
        c.executemany("INSERT INTO users (name) VALUES (?)", users)
    
    # Insert sample books with copies
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        books = [
            ('The Great Gatsby', 'F. Scott Fitzgerald', 'A classic novel of the Jazz Age', 1, 1),
            ('To Kill a Mockingbird', 'Harper Lee', 'A novel about race and class in 1930s Alabama', 1, 1),
            ('1984', 'George Orwell', 'Dystopian social science fiction novel', 3, 1),
            ('A Brief History of Time', 'Stephen Hawking', 'Popular science book about cosmology', 3, 1),
            ('Sapiens', 'Yuval Noah Harari', 'History of humankind', 2, 1)
        ]
        for book in books:
            c.execute(
                "INSERT INTO books (title, author, description, category_id, added_by) "
                "VALUES (?, ?, ?, ?, ?)",
                book
            )
            book_id = c.lastrowid
            # Add 2 copies for each book
            for _ in range(2):
                c.execute(
                    "INSERT INTO book_issue (book_id, added_by) VALUES (?, ?)",
                    (book_id, 1)
                )
    
    # Insert sample students
    c.execute("SELECT COUNT(*) FROM students")
    if c.fetchone()[0] == 0:
        students = [
            ('S001', 'John', 'Doe', 'john@example.com', 1, 1, 2023),
            ('S002', 'Jane', 'Smith', 'jane@example.com', 1, 1, 2023),
            ('S003', 'Robert', 'Johnson', 'robert@example.com', 2, 2, 2022),
            ('S004', 'Emily', 'Williams', 'emily@example.com', 1, 3, 2023)
        ]
        for student in students:
            c.execute(
                "INSERT INTO students (roll_num, first_name, last_name, email_id, category, branch, year) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                student
            )
    
    conn.commit()
    return conn

# Database connection
def connect_db():
    return init_db()

# --- Sidebar ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2991/2991108.png", width=100)
st.sidebar.markdown("## 📚 Library Management")
st.sidebar.markdown("---")

menu = ["🏠 Home", "📘 Book Management", "📤 Issue Management", "👨‍🎓 Student Management", "📊 Reports"]
choice = st.sidebar.radio("Navigation", menu)

conn = connect_db()
c = conn.cursor()

# --- Home ---
if choice == "🏠 Home":
    st.markdown("## 🏫 Welcome to the Library Dashboard")
    st.markdown("---")

    c.execute("SELECT COUNT(*) FROM books")
    book_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM students")
    student_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM book_issue WHERE available_status = 1")
    available_books = c.fetchone()[0]

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
        c.execute(
            "SELECT book_id, title, author, category_id FROM books "
            "WHERE title LIKE ? OR author LIKE ?",
            (f'%{search_term}%', f'%{search_term}%')
        )
        books = c.fetchall()
        if books:
            st.dataframe(pd.DataFrame(books, columns=["ID", "Title", "Author", "Category ID"]))
        else:
            st.warning("No books found.")

    with st.expander("➕ Add New Book"):
        with st.form("book_form"):
            title = st.text_input("Title", value="The Catcher in the Rye")
            author = st.text_input("Author", value="J.D. Salinger")
            description = st.text_area("Description", value="Coming-of-age novel about teenage angst")
            c.execute("SELECT id, category FROM book_categories")
            categories = {cat[1]: cat[0] for cat in c.fetchall()}
            category = st.selectbox("Category", options=categories.keys(), index=0)
            added_by = st.number_input("Added By (User ID)", min_value=1, value=1)

            submit_button = st.form_submit_button("✅ Add Book")
            if submit_button:
                category_id = categories[category]
                c.execute(
                    "INSERT INTO books (title, author, description, category_id, added_by) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (title, author, description, category_id, added_by)
                )
                # Add a copy to book_issue
                book_id = c.lastrowid
                c.execute(
                    "INSERT INTO book_issue (book_id, added_by) VALUES (?, ?)",
                    (book_id, added_by)
                )
                conn.commit()
                st.success("✅ Book added successfully!")

# --- Issue Management ---
elif choice == "📤 Issue Management":
    st.markdown("## 📤 Book Issue & Return")
    st.markdown("---")

    with st.expander("📦 Issue Book"):
        with st.form("issue_form"):
            c.execute("SELECT issue_id, book_id FROM book_issue WHERE available_status = 1")
            available_issues = c.fetchall()
            
            if available_issues:
                issue_options = {f"Book {issue[1]} (Copy {issue[0]})": issue[0] for issue in available_issues}
                issue_id = st.selectbox("Available Copies", options=list(issue_options.values()), 
                                        format_func=lambda x: list(issue_options.keys())[list(issue_options.values()).index(x)])

                c.execute("SELECT student_id, roll_num, first_name || ' ' || last_name FROM students")
                students = c.fetchall()
                student_options = {f"{s[1]} - {s[2]}": s[0] for s in students}
                student_id = st.selectbox("Student", options=list(student_options.values()), 
                                         format_func=lambda x: list(student_options.keys())[list(student_options.values()).index(x)])

                issue_days = st.number_input("Issue Duration (Days)", min_value=1, value=14)
                issued_by = st.number_input("Issued By (User ID)", min_value=1, value=1)

                submit_button = st.form_submit_button("📤 Issue Book")
                if submit_button:
                    issue_date = datetime.now()
                    return_date = issue_date + timedelta(days=issue_days)

                    c.execute("UPDATE book_issue SET available_status = 0 WHERE issue_id = ?", (issue_id,))
                    c.execute("INSERT INTO book_issue_log (book_issue_id, student_id, issue_by, issued_at, return_time) VALUES (?, ?, ?, ?, ?)",
                               (issue_id, student_id, issued_by, issue_date.strftime('%Y-%m-%d %H:%M:%S'), return_date.strftime('%Y-%m-%d %H:%M:%S')))
                    c.execute("UPDATE students SET books_issued = books_issued + 1 WHERE student_id = ?", (student_id,))
                    conn.commit()
                    st.success("✅ Book issued successfully!")
            else:
                st.warning("No available copies at the moment")
                st.form_submit_button("📤 Issue Book", disabled=True)

    with st.expander("📥 Return Book"):
        with st.form("return_form"):
            c.execute(
                "SELECT l.id, b.title, s.roll_num, s.first_name, s.last_name "
                "FROM book_issue_log l "
                "JOIN book_issue i ON l.book_issue_id = i.issue_id "
                "JOIN books b ON i.book_id = b.book_id "
                "JOIN students s ON l.student_id = s.student_id "
                "WHERE i.available_status = 0"
            )
            issued_books = c.fetchall()
            if not issued_books:
                st.warning("No books currently issued.")
                st.form_submit_button("📥 Return Book", disabled=True)
            else:
                issue_options = {f"{book[1]} to {book[2]} - {book[3]} {book[4]}": book[0] for book in issued_books}
                log_id = st.selectbox("Issued Books", options=list(issue_options.values()), 
                                      format_func=lambda x: list(issue_options.keys())[list(issue_options.values()).index(x)])

                submit_button = st.form_submit_button("📥 Return Book")
                if submit_button:
                    c.execute("SELECT book_issue_id, student_id FROM book_issue_log WHERE id = ?", (log_id,))
                    log_entry = c.fetchone()
                    c.execute("UPDATE book_issue SET available_status = 1 WHERE issue_id = ?", (log_entry[0],))
                    c.execute("UPDATE students SET books_issued = books_issued - 1 WHERE student_id = ?", (log_entry[1],))
                    conn.commit()
                    st.success("✅ Book returned successfully!")

# --- Student Management ---
elif choice == "👨‍🎓 Student Management":
    st.markdown("## 👨‍🎓 Student Management")
    st.markdown("---")

    c.execute(
        "SELECT s.student_id, s.roll_num, s.first_name, s.last_name, "
        "c.category, b.branch, s.books_issued, "
        "CASE WHEN s.approved = 1 THEN 'Approved' WHEN s.rejected = 1 THEN 'Rejected' ELSE 'Pending' END AS status "
        "FROM students s "
        "JOIN student_categories c ON s.category = c.cat_id "
        "JOIN branches b ON s.branch = b.id"
    )
    students = c.fetchall()
    if students:
        st.dataframe(pd.DataFrame(students, columns=["ID", "Roll No", "First Name", "Last Name", "Category", "Branch", "Books Issued", "Status"]))
    else:
        st.info("No students found.")

    with st.expander("➕ Add New Student"):
        with st.form("student_form"):
            first_name = st.text_input("First Name", value="Alex")
            last_name = st.text_input("Last Name", value="Johnson")
            roll_num = st.text_input("Roll Number", value="S005")
            email = st.text_input("Email", value="alex@example.com")

            c.execute("SELECT cat_id, category FROM student_categories")
            categories = {cat[1]: cat[0] for cat in c.fetchall()}
            category = st.selectbox("Category", options=categories.keys(), index=0)

            c.execute("SELECT id, branch FROM branches")
            branches = {branch[1]: branch[0] for branch in c.fetchall()}
            branch = st.selectbox("Branch", options=branches.keys(), index=0)

            year = st.number_input("Year", min_value=1900, max_value=2100, value=datetime.now().year)

            submit_button = st.form_submit_button("✅ Add Student")
            if submit_button:
                category_id = categories[category]
                branch_id = branches[branch]
                c.execute(
                    "INSERT INTO students (first_name, last_name, roll_num, email_id, category, branch, year) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
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
        c.execute("""
            SELECT b.title, s.roll_num, s.first_name || ' ' || s.last_name AS student_name,
                   l.issued_at, l.return_time,
                   (julianday('now') - julianday(l.return_time)) AS days_overdue
            FROM book_issue_log l
            JOIN book_issue i ON l.book_issue_id = i.issue_id
            JOIN books b ON i.book_id = b.book_id
            JOIN students s ON l.student_id = s.student_id
            WHERE l.return_time < datetime('now')
              AND i.available_status = 0
        """)
        overdue = c.fetchall()
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
        c.execute("""
            SELECT c.category, c.max_allowed, COUNT(s.student_id) AS students,
                   SUM(CASE WHEN s.books_issued >= c.max_allowed THEN 1 ELSE 0 END) AS exceeded_limit
            FROM student_categories c
            LEFT JOIN students s ON c.cat_id = s.category
            GROUP BY c.cat_id, c.category, c.max_allowed
        """)
        limits = c.fetchall()
        if limits:
            df = pd.DataFrame(limits, columns=["Category", "Max Allowed", "Total Students", "Exceeded Limit"])
            st.dataframe(df)

            st.bar_chart(df.set_index("Category")[["Total Students", "Exceeded Limit"]])
        else:
            st.warning("No borrowing data found.")

    # 3. 🧑‍💼 Librarian Performance
    with tab3:
        st.subheader("🧑‍💼 Librarian Performance")
        c.execute("""
            SELECT u.name, COUNT(l.id) AS books_issued,
                   SUM(CASE WHEN i.available_status = 0 THEN 1 ELSE 0 END) AS currently_borrowed
            FROM book_issue_log l
            JOIN users u ON l.issue_by = u.id
            JOIN book_issue i ON l.book_issue_id = i.issue_id
            GROUP BY u.id, u.name
        """)
        performance = c.fetchall()
        if performance:
            df = pd.DataFrame(performance, columns=["Librarian", "Total Issued", "Currently Borrowed"])
            st.dataframe(df)

            st.bar_chart(df.set_index("Librarian")[["Total Issued", "Currently Borrowed"]])
        else:
            st.warning("No librarian issue data yet.")


# --- Close connections ---
conn.close()
