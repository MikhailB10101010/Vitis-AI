/**
 * User Model (SQLite version)
 * Модель пользователя для системы аутентификации
 * 
 * Роли:
 * - user: базовый пользователь (оценка участков, отчеты)
 * - admin: администратор (+ управление моделями и данными)
 */

const { getDb } = require('../utils/database');

class User {
  constructor(userData) {
    if (userData) {
      this.id = userData.id || userData._id;
      this.username = userData.username;
      this.email = userData.email;
      this.password = userData.password;
      this.role = userData.role || 'user';
      this.fullName = userData.full_name || userData.fullName;
      this.organization = userData.organization;
      this.isActive = userData.is_active !== undefined ? userData.is_active : (userData.isActive !== undefined ? userData.isActive : true);
      this.isVerified = userData.is_verified !== undefined ? userData.is_verified : (userData.isVerified !== undefined ? userData.isVerified : false);
      this.lastLogin = userData.last_login || userData.lastLogin;
      this.evaluationCount = userData.evaluation_count !== undefined ? userData.evaluation_count : (userData.evaluationCount || 0);
      this.createdAt = userData.created_at || userData.createdAt;
      this.updatedAt = userData.updated_at || userData.updatedAt;
    }
  }

  static async create(userData) {
    const db = getDb();
    return await db.createUser(userData);
  }

  static async findByEmail(email) {
    const db = getDb();
    return await db.getUserByEmail(email);
  }

  static async findById(id) {
    const db = getDb();
    return await db.getUserById(id);
  }

  async comparePassword(candidatePassword) {
    const db = getDb();
    return await db.comparePassword(this, candidatePassword);
  }

  async updateLastLogin() {
    const db = getDb();
    await db.stmts.updateUserLastLogin.run(this.id);
    this.lastLogin = new Date().toISOString();
  }

  async save() {
    const db = getDb();
    await db.updateUserProfile(this.id, {
      fullName: this.fullName,
      organization: this.organization
    });
    this.updatedAt = new Date().toISOString();
  }

  toJSON() {
    const { password, ...userWithoutPassword } = this;
    return userWithoutPassword;
  }
}

module.exports = User;
