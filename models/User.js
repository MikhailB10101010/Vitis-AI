/**
 * User Model
 * Модель пользователя для системы аутентификации (SQLite)
 * 
 * Роли:
 * - user: базовый пользователь (оценка участков, отчеты)
 * - admin: администратор (+ управление моделями и данными)
 */

const Database = require('better-sqlite3');
const bcrypt = require('bcryptjs');
const path = require('path');

const dbPath = process.env.SQLITE_DB_PATH || path.join(__dirname, '..', 'data', 'vitis.db');

class User {
  constructor(db) {
    this.db = db;
    this.initTable();
  }

  initTable() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user' CHECK(role IN ('user', 'admin')),
        full_name TEXT,
        organization TEXT,
        is_active INTEGER DEFAULT 1,
        is_verified INTEGER DEFAULT 0,
        last_login DATETIME,
        evaluation_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    // Create indexes
    this.db.exec('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)');
    this.db.exec('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)');
    this.db.exec('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)');
  }

  async create(userData) {
    const { username, email, password, fullName, organization, role = 'user' } = userData;
    
    // Check if user exists
    const existing = this.db.prepare(
      'SELECT id FROM users WHERE email = ? OR username = ?'
    ).get(email.toLowerCase().trim(), username.trim());
    
    if (existing) {
      const existingUser = this.db.prepare(
        'SELECT email, username FROM users WHERE id = ?'
      ).get(existing.id);
      
      if (existingUser.email === email.toLowerCase().trim()) {
        throw new Error('Email already registered');
      } else {
        throw new Error('Username already taken');
      }
    }

    // Hash password
    const salt = bcrypt.genSaltSync(process.env.BCRYPT_ROUNDS || 10);
    const hashedPassword = bcrypt.hashSync(password, salt);

    const stmt = this.db.prepare(`
      INSERT INTO users (username, email, password, role, full_name, organization, is_active)
      VALUES (?, ?, ?, ?, ?, ?, 1)
    `);

    const result = stmt.run(
      username.trim(),
      email.toLowerCase().trim(),
      hashedPassword,
      role,
      fullName?.trim() || null,
      organization?.trim() || null
    );

    return this.findById(result.lastInsertRowid);
  }

  findById(id) {
    const user = this.db.prepare('SELECT * FROM users WHERE id = ?').get(id);
    if (!user) return null;
    
    return {
      _id: user.id,
      id: user.id,
      username: user.username,
      email: user.email,
      role: user.role,
      fullName: user.full_name,
      organization: user.organization,
      isActive: user.is_active === 1,
      isVerified: user.is_verified === 1,
      lastLogin: user.last_login,
      evaluationCount: user.evaluation_count,
      createdAt: user.created_at,
      updatedAt: user.updated_at
    };
  }

  findByEmail(email) {
    const user = this.db.prepare('SELECT * FROM users WHERE email = ?').get(email.toLowerCase().trim());
    if (!user) return null;
    
    return {
      _id: user.id,
      id: user.id,
      username: user.username,
      email: user.email,
      password: user.password,
      role: user.role,
      fullName: user.full_name,
      organization: user.organization,
      isActive: user.is_active === 1,
      isVerified: user.is_verified === 1,
      lastLogin: user.last_login,
      evaluationCount: user.evaluation_count,
      createdAt: user.created_at,
      updatedAt: user.updated_at,
      comparePassword: async (candidatePassword) => {
        return bcrypt.compareSync(candidatePassword, user.password);
      },
      updateLastLogin: async () => {
        const stmt = this.db.prepare('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?');
        stmt.run(user.id);
      }
    };
  }

  toJSON(user) {
    if (!user) return null;
    const { password, ...rest } = user;
    return rest;
  }
}

// Singleton instance
let dbInstance = null;
let userModelInstance = null;

function getDb() {
  if (!dbInstance) {
    dbInstance = new Database(dbPath);
    dbInstance.pragma('journal_mode = WAL');
  }
  return dbInstance;
}

function getUserModel() {
  if (!userModelInstance) {
    userModelInstance = new User(getDb());
  }
  return userModelInstance;
}

module.exports = getUserModel();
module.exports.getUserModel = getUserModel;
module.exports.getDb = getDb;
