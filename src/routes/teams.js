const express = require('express');
const router = express.Router();
const Database = require('../models/database');

// 创建数据库实例
let db;

// 中间件：确保数据库连接
router.use((req, res, next) => {
    if (!db) {
        const dbPath = req.app.get('dbPath');
        if (!dbPath) {
            return res.status(500).render('error', { 
                message: '数据库路径未配置',
                error: { stack: '数据库路径未在应用程序中配置' }
            });
        }
        db = new Database(dbPath);
    }
    next();
});

// 关闭数据库连接
async function closeDatabase() {
    if (db) {
        await db.close();
        db = null;
    }
}

// 导出关闭数据库方法
router.closeDatabase = closeDatabase;

// 获取球队列表
router.get('/', async (req, res, next) => {
    try {
        const keyword = req.query.search;
        const teams = keyword ? 
            await db.searchTeams(keyword) : 
            await db.getAllTeams();
            
        res.render('teams/index', { 
            teams,
            searchKeyword: keyword || ''
        });
    } catch (err) {
        next(err);
    }
});

// 获取球队详情
router.get('/:id', async (req, res, next) => {
    try {
        const team = await db.getTeam(req.params.id);
        const staff = await db.getTeamStaff(req.params.id);
        
        if (!team) {
            return res.status(404).render('error', { 
                message: '未找到该球队',
                error: { stack: `ID为 ${req.params.id} 的球队不存在` }
            });
        }
        
        res.render('teams/detail', { team, staff });
    } catch (err) {
        next(err);
    }
});

// 更新球队信息
router.post('/:id', async (req, res, next) => {
    try {
        const teamId = req.params.id;
        await db.updateTeam(teamId, req.body);
        
        // 添加成功消息到session
        req.session.flash = {
            type: 'success',
            message: '球队信息已成功更新'
        };
        
        res.redirect(`/teams/${teamId}`);
    } catch (err) {
        next(err);
    }
});

module.exports = router; 