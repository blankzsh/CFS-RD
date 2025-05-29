const express = require('express');
const router = express.Router();
const Database = require('../models/database');

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

// 获取员工列表
router.get('/', async (req, res, next) => {
    try {
        const keyword = req.query.search;
        const staff = keyword ? 
            await db.searchStaff(keyword) : 
            await db.getAllStaff();
            
        res.render('staff/index', { 
            staff,
            searchKeyword: keyword || ''
        });
    } catch (err) {
        next(err);
    }
});

// 获取员工详情
router.get('/:id', async (req, res, next) => {
    try {
        const staff = await db.getStaff(req.params.id);
        
        if (!staff) {
            return res.status(404).render('error', { 
                message: '未找到该员工',
                error: { stack: `ID为 ${req.params.id} 的员工不存在` }
            });
        }
        
        res.render('staff/detail', { staff });
    } catch (err) {
        next(err);
    }
});

// 更新员工信息
router.post('/:id', async (req, res, next) => {
    try {
        const staffId = req.params.id;
        
        // 验证请求数据
        const { name, ability, fame } = req.body;
        if (!name || name.trim() === '') {
            return res.status(400).json({ error: '姓名不能为空' });
        }
        
        const abilityNum = parseInt(ability);
        if (isNaN(abilityNum) || abilityNum < 0 || abilityNum > 100) {
            return res.status(400).json({ error: '能力值必须在0-100之间' });
        }
        
        const fameNum = parseInt(fame);
        if (isNaN(fameNum) || fameNum < 0) {
            return res.status(400).json({ error: '知名度必须大于等于0' });
        }
        
        // 更新数据库
        await db.updateStaff(staffId, {
            name: name.trim(),
            ability: abilityNum,
            fame: fameNum
        });
        
        res.json({ success: true });
    } catch (err) {
        console.error('更新员工信息失败:', err);
        res.status(500).json({ 
            error: '更新员工信息失败: ' + (err.message || '未知错误') 
        });
    }
});

module.exports = router; 