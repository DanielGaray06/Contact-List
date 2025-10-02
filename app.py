from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app=Flask(__name__)

app.config['DATABASE'] = "mydatabase.db"
app.secret_key="password"

def get_db_connection():
    conn = sqlite3.connect (app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
                SELECT * FROM contacts
                """) 
    data = cur.fetchall()
    return render_template('index.html', contacts = data)

@app.route ('/add_contact', methods=['POST'])
def add():
    if request.method == 'POST':
        fullname = request.form['fullname']
        phone = request.form['phone']
        email = request.form['email']
        conn= get_db_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO contacts (fullname, phone, email)
        VALUES (?, ?, ?)
    """, (fullname, phone, email))   
        flash('Contacts added successfully')
    conn.commit()
    return redirect(url_for('index'))

@app.route('/edit/<id>')
def get_contact (id):
    conn = get_db_connection()
    cur=conn.cursor()
    cur.execute(' SELECT * FROM contacts WHERE id = ?', (id))
    data = cur.fetchall()
    return render_template('edit-contact.html', contact = data[0])

@app.route('/update/<int:id>', methods=['POST'])
def update_contact(id):
    if request.method == 'POST':
        fullname = request.form ['fullname']
        phone = request.form ['phone']
        email = request.form ['email']
        
        conn = get_db_connection()
        cur=conn.cursor()
        cur.execute(""" 
                    UPDATE contacts
                    SET fullname = ?, phone = ?, email =?
                    WHERE id = ?
                    """, (fullname, phone, email, id))
        conn.commit()
        flash ('Contact Updated Successfully')
        return redirect(url_for('index'))
        
@app.route('/delete/<string:id>' )
def delete(id):
    conn = get_db_connection()
    cur= conn.cursor()
    cur.execute('DELETE FROM contacts WHERE id = ?', (id,))
    conn.commit()
    conn.close
    flash ('Contact Removed Succesfull')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
