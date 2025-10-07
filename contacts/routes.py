from flask import Blueprint, render_template, request, redirect, url_for, flash
from .db import get_db_connection
from sqlite3 import IntegrityError

contacts_bp = Blueprint('contacts', __name__, url_prefix='/')

@contacts_bp.route('/')
def index():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
                    SELECT * FROM contacts
                    """) 
        data = cur.fetchall()
        return render_template('index.html', contacts = data)

@contacts_bp.route ('/add_contact', methods=['POST'])
def add():
        if request.method == 'POST':
            fullname = request.form['fullname']
            phone = request.form['phone']
            email = request.form['email']
        
        if not fullname or not phone or not email:
            flash('All fields are required!', 'error')
            return redirect(url_for('index'))   
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO contacts (fullname, phone, email) VALUES (?, ?, ?)',
                (fullname, phone, email)
            )
            conn.commit()
            flash('Contact added successfully!', 'success')

        except IntegrityError as e:
            if 'UNIQUE constraint failed' in str(e):
                flash('This email already exists.', 'error')
            else:
                flash('Database integrity error. Please check your data.', 'error')
            
        except Exception as e:
            flash(f'Unexpected error: {e}', 'error')

        finally:
            conn.close()

        return redirect(url_for('contacts.index'))

@contacts_bp.route('/edit/<id>')
def get_contact (id):
    conn = get_db_connection()
    cur=conn.cursor()
    cur.execute(' SELECT * FROM contacts WHERE id = ?', (id))
    data = cur.fetchall()
    return render_template('edit-contact.html', contact = data[0])

@contacts_bp.route('/update/<int:id>', methods=['POST'])
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
    
@contacts_bp.route('/delete/<string:id>' )
def delete(id):
    conn = get_db_connection()
    cur= conn.cursor()
    cur.execute('DELETE FROM contacts WHERE id = ?', (id,))
    conn.commit()
    conn.close
    flash ('Contact Removed Succesfull')
    return redirect(url_for('index'))
