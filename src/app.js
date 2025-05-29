const express = require('express');
const path = require('path');
const session = require('express-session');
const multer = require('multer');
const expressLayouts = require('express-ejs-layouts');
const fs = require('fs');
const os = require('os');
const { v4: uuidv4 } = require('uuid');

// 创建Express应用
const app = express();

// 配置模板引擎和布局
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(expressLayouts);
app.set('layout', 'layouts/default');

// 配置中间件
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 配置静态文件
app.use(express.static(path.join(__dirname, 'public'), {
    setHeaders: (res, path, stat) => {
        if (path.endsWith('.css')) {
            res.set('Content-Type', 'text/css');
        } else if (path.endsWith('.js')) {
            res.set('Content-Type', 'application/javascript');
        }
    }
}));

// 配置session
app.use(session({
    secret: 'cfs-web-secret',
    resave: false,
    saveUninitialized: true,
    cookie: { secure: process.env.NODE_ENV === 'production' }
}));

// 确保必要的目录存在
const dirs = [
    path.join(__dirname, 'uploads', 'temp')
];

dirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
});

// 配置数据库文件上传
const dbStorage = multer.diskStorage({
    destination: function (req, file, cb) {
        // 使用项目内的临时目录
        const tempDir = path.join(__dirname, 'uploads', 'temp');
        cb(null, tempDir);
    },
    filename: function (req, file, cb) {
        // 生成唯一的临时文件名
        const uniqueName = `${uuidv4()}-${file.originalname}`;
        cb(null, uniqueName);
    }
});

const dbUpload = multer({ 
    storage: dbStorage,
    fileFilter: (req, file, cb) => {
        // 只允许.db文件
        if (file.originalname.toLowerCase().endsWith('.db')) {
            cb(null, true);
        } else {
            cb(new Error('只允许上传.db文件'));
        }
    }
});

// 存储当前使用的数据库文件路径
let currentDbPath = null;

// 清理临时文件的函数
async function cleanupTempFile(filePath) {
    if (filePath && fs.existsSync(filePath)) {
        try {
            // 如果是数据库文件，先关闭连接
            if (filePath === app.get('dbPath')) {
                const routes = require('./routes');
                if (routes.staff && routes.staff.closeDatabase) {
                    await routes.staff.closeDatabase();
                }
                if (routes.teams && routes.teams.closeDatabase) {
                    await routes.teams.closeDatabase();
                }
                app.set('dbPath', null);
            }

            // 等待一小段时间确保连接完全关闭
            await new Promise(resolve => setTimeout(resolve, 100));

            // 删除主数据库文件
            await fs.promises.unlink(filePath);
            console.log('已清理临时文件:', filePath);

            // 删除相关的WAL和SHM文件
            const walFile = `${filePath}-wal`;
            const shmFile = `${filePath}-shm`;
            
            if (fs.existsSync(walFile)) {
                await fs.promises.unlink(walFile);
                console.log('已清理WAL文件:', walFile);
            }
            if (fs.existsSync(shmFile)) {
                await fs.promises.unlink(shmFile);
                console.log('已清理SHM文件:', shmFile);
            }
        } catch (err) {
            console.error('清理临时文件失败:', err);
            // 不抛出错误，继续执行
        }
    }
}

// 清理所有临时文件
async function cleanupAllTempFiles() {
    const tempDir = path.join(__dirname, 'uploads', 'temp');
    if (fs.existsSync(tempDir)) {
        try {
            const files = await fs.promises.readdir(tempDir);
            
            for (const file of files) {
                const filePath = path.join(tempDir, file);
                if (filePath !== currentDbPath) {  // 不删除当前使用的文件
                    await cleanupTempFile(filePath);
                }
            }
        } catch (err) {
            console.error('读取临时目录失败:', err);
        }
    }
}

// 定期清理临时文件（每小时执行一次）
setInterval(cleanupAllTempFiles, 3600000);

// 路由配置
const teamRoutes = require('./routes/teams');
const staffRoutes = require('./routes/staff');

// 首页路由
app.get('/', (req, res) => {
    // 启动时清理旧的临时文件
    cleanupAllTempFiles();
    
    res.render('index', { 
        dbPath: app.get('dbPath') || null
    });
});

// 数据库选择API
app.post('/api/database/select', dbUpload.single('database'), (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: '请选择数据库文件' });
        }

        // 清理之前的临时文件
        if (currentDbPath) {
            cleanupTempFile(currentDbPath);
        }

        // 保存新的临时文件路径
        currentDbPath = req.file.path;
        app.set('dbPath', currentDbPath);

        // 设置退出处理程序（如果还没有设置）
        if (!app.get('exitHandlerSet')) {
            process.on('exit', () => {
                cleanupTempFile(currentDbPath);
                cleanupAllTempFiles();
            });
            process.on('SIGINT', () => {
                cleanupTempFile(currentDbPath);
                cleanupAllTempFiles();
                process.exit();
            });
            app.set('exitHandlerSet', true);
        }

        res.json({ success: true, dbPath: currentDbPath });
    } catch (err) {
        if (req.file) {
            cleanupTempFile(req.file.path);
        }
        res.status(500).json({ error: err.message });
    }
});

// 数据库导出API
app.get('/api/database/export', (req, res) => {
    try {
        const dbPath = app.get('dbPath');
        if (!dbPath) {
            return res.status(400).json({ error: '未连接数据库' });
        }

        // 生成导出文件名
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const exportFileName = `CFS_Database_${timestamp}.db`;

        // 设置响应头
        res.setHeader('Content-Type', 'application/octet-stream');
        res.setHeader('Content-Disposition', `attachment; filename="${exportFileName}"`);

        // 创建文件读取流并通过管道传输到响应
        const fileStream = fs.createReadStream(dbPath);
        fileStream.pipe(res);

    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 退出数据库API
app.post('/api/database/exit', async (req, res) => {
    try {
        const dbPath = app.get('dbPath');
        if (!dbPath) {
            return res.status(400).json({ error: '未连接数据库' });
        }

        // 清理当前数据库文件
        await cleanupTempFile(currentDbPath);
        
        // 重置数据库路径
        currentDbPath = null;

        res.json({ success: true, message: '已成功退出数据库' });
    } catch (err) {
        console.error('退出数据库失败:', err);
        res.status(500).json({ error: err.message });
    }
});

app.use('/teams', teamRoutes);
app.use('/staff', staffRoutes);

// 错误处理中间件
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).render('error', { 
        message: '服务器发生错误',
        error: process.env.NODE_ENV === 'development' ? err : {}
    });
});

// 启动服务器
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`服务器运行在 http://localhost:${PORT}`);
}); 