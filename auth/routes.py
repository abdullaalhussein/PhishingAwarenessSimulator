import bcrypt
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from auth import auth_bp
from auth.forms import RegistrationForm, LoginForm
from models import db, User


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        password_hash = bcrypt.hashpw(
            form.password.data.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=password_hash,
            role=form.role.data,
        )
        db.session.add(user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.checkpw(
            form.password.data.encode('utf-8'),
            user.password_hash.encode('utf-8')
        ):
            login_user(user)
            next_page = request.args.get('next')
            flash('Logged in successfully.', 'success')
            return redirect(next_page or url_for('dashboard.index'))

        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
