from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, random, string
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fb3-ultra-secret-2026')
DATABASE = 'fb3.db'

# ── Harvey Quotes ─────────────────────────────────────────────────────────────
HARVEY_QUOTES = [
    "I don't have dreams, I have goals.",
    "Work until you no longer have to introduce yourself.",
    "When you're backed against the wall, break the goddamn thing down.",
    "The only time success comes before work is in the dictionary.",
    "Kill them with success and bury them with a smile.",
    "Winners don't make excuses when the other side plays the game.",
    "Let them underestimate you. That's when you strike.",
    "Competence is the baseline. Confidence is the weapon.",
    "Never destroy anyone in public when you can accomplish the same result in private.",
    "The best way to get what you want is to deserve what you want.",
    "Don't raise your voice. Improve your argument.",
    "Anyone can do my job, but no one can be me.",
    "Win your morning. Win your day.",
    "Stop being perfect. Be better.",
    "You always have a choice.",
    "Loyalty is a two-way street.",
    "First impressions last. Make yours count.",
    "I refuse to answer that on the grounds that I don't want to.",
    "Catch me if you can, but you can't.",
    "I'm not the best because I win every fight. I'm the best because I choose which fights to have.",
]

# ── Ranks ─────────────────────────────────────────────────────────────────────
def get_rank(wins):
    if wins >= 100: return ('Legend', '👑')
    if wins >= 50:  return ('Elite', '⚡')
    if wins >= 25:  return ('Warrior', '🔥')
    if wins >= 10:  return ('Grinder', '💪')
    return ('Rookie', '🌱')

def get_xp(wins, losses, streak, sessions_today):
    return (wins * 100) + (streak * 50) - (losses * 10) + (sessions_today * 25)

# ── Badges ────────────────────────────────────────────────────────────────────
def get_badges(user):
    badges = []
    hour = datetime.now().hour
    if hour >= 22 or hour < 4:   badges.append(('🦉', 'Night Owl'))
    if hour >= 5 and hour < 8:   badges.append(('🌅', 'Early Bird'))
    if user['streak'] >= 10:     badges.append(('⚡', 'Unstoppable'))
    if user['wins'] >= 50:       badges.append(('👑', 'Legend'))
    if user['best_streak'] >= 7: badges.append(('🔥', 'On Fire'))
    return badges

# ── DB ────────────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            wins          INTEGER DEFAULT 0,
            losses        INTEGER DEFAULT 0,
            streak        INTEGER DEFAULT 0,
            best_streak   INTEGER DEFAULT 0,
            xp            INTEGER DEFAULT 0,
            theme         TEXT    DEFAULT 'theme-lofi',
            daily_goal    INTEGER DEFAULT 3,
            sessions_today INTEGER DEFAULT 0,
            last_session_date TEXT DEFAULT '',
            comeback_mode INTEGER DEFAULT 0,
            loss_streak   INTEGER DEFAULT 0,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS groups_table (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            code       TEXT UNIQUE NOT NULL,
            creator_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS group_members (
            group_id   INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            joined_at  TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS activity_feed (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            group_id   INTEGER NOT NULL,
            message    TEXT NOT NULL,
            type       TEXT DEFAULT 'win',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            duration   INTEGER NOT NULL,
            category   TEXT DEFAULT 'General',
            result     TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

def current_user():
    uid = session.get('user_id')
    if not uid: return None
    conn = get_db()
    u = conn.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()
    conn.close()
    return u

def login_required(f):
    from functools import wraps
    @wraps(f)
    def dec(*a, **kw):
        if not session.get('user_id'): return redirect(url_for('login'))
        return f(*a, **kw)
    return dec

def reset_daily_if_needed(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    today = str(date.today())
    if user['last_session_date'] != today:
        conn.execute('UPDATE users SET sessions_today = 0, last_session_date = ? WHERE id = ?', (today, user_id))
        conn.commit()
    conn.close()

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('dashboard') if session.get('user_id') else url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if not user or not check_password_hash(user['password_hash'], password):
            error = 'Invalid username or password.'
        else:
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if len(username) < 3: error = 'Username min 3 chars.'
        elif len(password) < 6: error = 'Password min 6 chars.'
        else:
            conn = get_db()
            if conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
                error = 'Username taken.'
            else:
                conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                             (username, generate_password_hash(password)))
                conn.commit()
                user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
                session['user_id'] = user['id']
                conn.close()
                return redirect(url_for('dashboard'))
            conn.close()
    return render_template('signup.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Pages ─────────────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    reset_daily_if_needed(user['id'])
    user = current_user()
    rank_name, rank_icon = get_rank(user['wins'])
    badges = get_badges(user)
    xp = get_xp(user['wins'], user['losses'], user['streak'], user['sessions_today'])
    total = user['wins'] + user['losses']
    wr = round(user['wins'] / total * 100, 1) if total > 0 else 0
    return render_template('dashboard.html', user=user, rank_name=rank_name,
                           rank_icon=rank_icon, badges=badges, xp=xp, wr=wr)

@app.route('/timer')
@login_required
def timer():
    user = current_user()
    duration = request.args.get('duration', '25')
    category = request.args.get('category', 'General')
    quote = random.choice(HARVEY_QUOTES)
    return render_template('timer.html', user=user, duration=duration,
                           category=category, quote=quote)

@app.route('/leaderboard')
@login_required
def leaderboard():
    conn = get_db()
    top = conn.execute(
        'SELECT username, wins, losses, streak, best_streak FROM users ORDER BY wins DESC LIMIT 20'
    ).fetchall()
    conn.close()
    users_data = []
    for u in top:
        rn, ri = get_rank(u['wins'])
        users_data.append({'user': u, 'rank_name': rn, 'rank_icon': ri})
    return render_template('leaderboard.html', users_data=users_data, current_user=current_user())

@app.route('/groups')
@login_required
def groups():
    user = current_user()
    conn = get_db()
    my_groups = conn.execute('''
        SELECT g.*, u.username as creator_name,
               (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count
        FROM groups_table g
        JOIN group_members gm ON g.id = gm.group_id
        JOIN users u ON g.creator_id = u.id
        WHERE gm.user_id = ?
        ORDER BY g.created_at DESC
    ''', (user['id'],)).fetchall()
    conn.close()
    return render_template('groups.html', user=user, my_groups=my_groups)

@app.route('/groups/<int:group_id>')
@login_required
def group_detail(group_id):
    user = current_user()
    conn = get_db()
    group = conn.execute('SELECT * FROM groups_table WHERE id = ?', (group_id,)).fetchone()
    if not group:
        conn.close()
        return redirect(url_for('groups'))
    is_member = conn.execute(
        'SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, user['id'])
    ).fetchone()
    if not is_member:
        conn.close()
        return redirect(url_for('groups'))
    members = conn.execute('''
        SELECT u.username, u.wins, u.losses, u.streak, u.best_streak
        FROM users u
        JOIN group_members gm ON u.id = gm.user_id
        WHERE gm.group_id = ?
        ORDER BY u.wins DESC
    ''', (group_id,)).fetchall()
    feed = conn.execute('''
        SELECT af.message, af.type, af.created_at, u.username
        FROM activity_feed af
        JOIN users u ON af.user_id = u.id
        WHERE af.group_id = ?
        ORDER BY af.created_at DESC
        LIMIT 20
    ''', (group_id,)).fetchall()
    conn.close()
    members_data = []
    for m in members:
        rn, ri = get_rank(m['wins'])
        members_data.append({'member': m, 'rank_name': rn, 'rank_icon': ri})
    is_creator = group['creator_id'] == user['id']
    return render_template('group_detail.html', user=user, group=group,
                           members_data=members_data, feed=feed, is_creator=is_creator)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=current_user())

# ── Group API ─────────────────────────────────────────────────────────────────
@app.route('/api/groups/create', methods=['POST'])
@login_required
def create_group():
    user = current_user()
    name = request.json.get('name', '').strip()
    if not name: return jsonify({'error': 'Name required'}), 400
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    conn = get_db()
    conn.execute('INSERT INTO groups_table (name, code, creator_id) VALUES (?, ?, ?)',
                 (name, code, user['id']))
    conn.commit()
    group = conn.execute('SELECT * FROM groups_table WHERE code = ?', (code,)).fetchone()
    conn.execute('INSERT INTO group_members (group_id, user_id) VALUES (?, ?)',
                 (group['id'], user['id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'code': code, 'group_id': group['id']})

@app.route('/api/groups/join', methods=['POST'])
@login_required
def join_group():
    user = current_user()
    code = request.json.get('code', '').strip().upper()
    conn = get_db()
    group = conn.execute('SELECT * FROM groups_table WHERE code = ?', (code,)).fetchone()
    if not group:
        conn.close()
        return jsonify({'error': 'Invalid code'}), 404
    existing = conn.execute(
        'SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?', (group['id'], user['id'])
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'Already a member'}), 400
    conn.execute('INSERT INTO group_members (group_id, user_id) VALUES (?, ?)', (group['id'], user['id']))
    # Add join activity
    conn.execute('INSERT INTO activity_feed (user_id, group_id, message, type) VALUES (?, ?, ?, ?)',
                 (user['id'], group['id'], f"{user['username']} joined the group 👋", 'join'))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'group_id': group['id'], 'name': group['name']})

# ── Session API ───────────────────────────────────────────────────────────────
@app.route('/api/session/win', methods=['POST'])
@login_required
def session_win():
    user_id = session['user_id']
    data = request.json or {}
    duration = data.get('duration', 25)
    category = data.get('category', 'General')
    xp_gain = duration * 4

    conn = get_db()
    conn.execute('''UPDATE users SET wins = wins + 1, streak = streak + 1,
                    sessions_today = sessions_today + 1, xp = xp + ?,
                    loss_streak = 0, comeback_mode = 0,
                    last_session_date = ?
                    WHERE id = ?''', (xp_gain, str(date.today()), user_id))
    conn.execute('UPDATE users SET best_streak = streak WHERE id = ? AND streak > best_streak', (user_id,))
    conn.commit()

    # Log session
    conn.execute('INSERT INTO sessions_log (user_id, duration, category, result) VALUES (?, ?, ?, ?)',
                 (user_id, duration, category, 'win'))
    conn.commit()

    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    # Post to all groups
    groups = conn.execute(
        'SELECT group_id FROM group_members WHERE user_id = ?', (user_id,)
    ).fetchall()
    msg = f"{user['username']} won a {duration}min {category} session 🏆"
    for g in groups:
        conn.execute('INSERT INTO activity_feed (user_id, group_id, message, type) VALUES (?, ?, ?, ?)',
                     (user_id, g['group_id'], msg, 'win'))
    conn.commit()
    conn.close()

    rn, ri = get_rank(user['wins'])
    return jsonify({'status': 'win', 'wins': user['wins'], 'losses': user['losses'],
                    'streak': user['streak'], 'best_streak': user['best_streak'],
                    'xp': user['xp'], 'xp_gain': xp_gain, 'rank': rn, 'rank_icon': ri})

@app.route('/api/session/loss', methods=['POST'])
@login_required
def session_loss():
    user_id = session['user_id']
    data = request.json or {}
    duration = data.get('duration', 25)
    category = data.get('category', 'General')

    conn = get_db()
    conn.execute('''UPDATE users SET losses = losses + 1, streak = 0,
                    loss_streak = loss_streak + 1,
                    last_session_date = ?
                    WHERE id = ?''', (str(date.today()), user_id))
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    # Comeback mode after 3 losses in a row
    if user['loss_streak'] >= 3:
        conn.execute('UPDATE users SET comeback_mode = 1 WHERE id = ?', (user_id,))

    conn.execute('INSERT INTO sessions_log (user_id, duration, category, result) VALUES (?, ?, ?, ?)',
                 (user_id, duration, category, 'loss'))

    groups = conn.execute('SELECT group_id FROM group_members WHERE user_id = ?', (user_id,)).fetchall()
    msg = f"{user['username']} abandoned a {duration}min session 💀"
    for g in groups:
        conn.execute('INSERT INTO activity_feed (user_id, group_id, message, type) VALUES (?, ?, ?, ?)',
                     (user_id, g['group_id'], msg, 'loss'))
    conn.commit()
    conn.close()
    return jsonify({'status': 'loss', 'wins': user['wins'], 'losses': user['losses'],
                    'streak': user['streak'], 'loss_streak': user['loss_streak']})

@app.route('/api/theme', methods=['POST'])
@login_required
def save_theme():
    theme = request.json.get('theme', 'theme-lofi')
    conn = get_db()
    conn.execute('UPDATE users SET theme = ? WHERE id = ?', (theme, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/daily-goal', methods=['POST'])
@login_required
def set_daily_goal():
    goal = request.json.get('goal', 3)
    conn = get_db()
    conn.execute('UPDATE users SET daily_goal = ? WHERE id = ?', (goal, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
