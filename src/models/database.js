const sqlite3 = require('sqlite3').verbose();
const path = require('path');

class Database {
    constructor(dbPath) {
        this.db = new sqlite3.Database(dbPath, (err) => {
            if (err) {
                console.error('数据库连接错误:', err);
            } else {
                console.log('数据库连接成功');
            }
        });
    }

    // 获取所有球队
    getAllTeams() {
        return new Promise((resolve, reject) => {
            const query = `
                SELECT T.*, L.LeagueName 
                FROM Teams T
                LEFT JOIN League L ON T.BelongingLeague = L.ID
                ORDER BY T.TeamName
            `;
            this.db.all(query, [], (err, rows) => {
                if (err) reject(err);
                else resolve(rows);
            });
        });
    }

    // 获取单个球队信息
    getTeam(id) {
        return new Promise((resolve, reject) => {
            const query = `
                SELECT T.*, L.LeagueName 
                FROM Teams T
                LEFT JOIN League L ON T.BelongingLeague = L.ID
                WHERE T.ID = ?
            `;
            this.db.get(query, [id], (err, row) => {
                if (err) reject(err);
                else resolve(row);
            });
        });
    }

    // 更新球队信息
    updateTeam(id, data) {
        return new Promise((resolve, reject) => {
            const fields = Object.keys(data).filter(key => key !== 'ID');
            const values = fields.map(field => data[field]);
            const query = `
                UPDATE Teams 
                SET ${fields.map(field => `${field} = ?`).join(', ')}
                WHERE ID = ?
            `;
            this.db.run(query, [...values, id], function(err) {
                if (err) reject(err);
                else resolve(this.changes);
            });
        });
    }

    // 获取球队员工
    getTeamStaff(teamId) {
        return new Promise((resolve, reject) => {
            const query = `
                SELECT * FROM Staff 
                WHERE EmployedTeamID = ?
                ORDER BY Name
            `;
            this.db.all(query, [teamId], (err, rows) => {
                if (err) reject(err);
                else resolve(rows);
            });
        });
    }

    // 获取所有员工
    getAllStaff() {
        return new Promise((resolve, reject) => {
            const query = `
                SELECT S.*, T.TeamName
                FROM Staff S
                LEFT JOIN Teams T ON S.EmployedTeamID = T.ID
                ORDER BY S.Name
            `;
            this.db.all(query, [], (err, rows) => {
                if (err) reject(err);
                else resolve(rows);
            });
        });
    }

    // 获取单个员工信息
    getStaff(id) {
        return new Promise((resolve, reject) => {
            const query = `
                SELECT S.*, T.TeamName, T.ID as TeamID
                FROM Staff S
                LEFT JOIN Teams T ON S.EmployedTeamID = T.ID
                WHERE S.ID = ?
            `;
            this.db.get(query, [id], (err, row) => {
                if (err) reject(err);
                else resolve(row);
            });
        });
    }

    // 搜索员工
    searchStaff(keyword) {
        return new Promise((resolve, reject) => {
            const query = `
                SELECT S.*, T.TeamName
                FROM Staff S
                LEFT JOIN Teams T ON S.EmployedTeamID = T.ID
                WHERE S.Name LIKE ?
                ORDER BY S.Name
            `;
            const searchPattern = `%${keyword}%`;
            this.db.all(query, [searchPattern], (err, rows) => {
                if (err) reject(err);
                else resolve(rows);
            });
        });
    }

    // 更新员工信息
    updateStaff(id, data) {
        return new Promise((resolve, reject) => {
            try {
                // 验证数据
                if (!data.name || typeof data.name !== 'string') {
                    throw new Error('无效的姓名');
                }
                if (typeof data.ability !== 'number' || data.ability < 0 || data.ability > 100) {
                    throw new Error('无效的能力值');
                }
                if (typeof data.fame !== 'number' || data.fame < 0) {
                    throw new Error('无效的知名度');
                }

                const query = `
                    UPDATE Staff 
                    SET Name = ?, AbilityJSON = ?, Fame = ?
                    WHERE ID = ?
                `;
                
                // 创建能力值JSON
                const abilityJSON = JSON.stringify({
                    rawAbility: data.ability
                });
                
                this.db.run(query, [data.name, abilityJSON, data.fame, id], function(err) {
                    if (err) {
                        console.error('数据库更新失败:', err);
                        reject(new Error('数据库更新失败'));
                    } else if (this.changes === 0) {
                        reject(new Error('未找到要更新的员工'));
                    } else {
                        resolve(this.changes);
                    }
                });
            } catch (err) {
                reject(err);
            }
        });
    }

    // 搜索球队
    searchTeams(keyword) {
        return new Promise((resolve, reject) => {
            const query = `
                SELECT T.*, L.LeagueName 
                FROM Teams T
                LEFT JOIN League L ON T.BelongingLeague = L.ID
                WHERE T.TeamName LIKE ? 
                   OR T.Nickname LIKE ?
                   OR T.TeamLocation LIKE ?
                ORDER BY T.TeamName
            `;
            const searchPattern = `%${keyword}%`;
            this.db.all(query, [searchPattern, searchPattern, searchPattern], (err, rows) => {
                if (err) reject(err);
                else resolve(rows);
            });
        });
    }

    // 关闭数据库连接
    close() {
        return new Promise((resolve, reject) => {
            this.db.close((err) => {
                if (err) reject(err);
                else resolve();
            });
        });
    }
}

module.exports = Database; 