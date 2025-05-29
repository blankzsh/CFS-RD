const fs = require('fs');
const path = require('path');

// 创建必要的目录
const dirs = [
    'src/public/css',
    'src/public/js',
    'src/public/images',
    'src/public/images/logos'
];

dirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`创建目录: ${dir}`);
    }
});

// 复制Bootstrap文件
const files = [
    {
        src: 'node_modules/bootstrap/dist/css/bootstrap.min.css',
        dest: 'src/public/css/bootstrap.min.css'
    },
    {
        src: 'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js',
        dest: 'src/public/js/bootstrap.bundle.min.js'
    }
];

files.forEach(file => {
    fs.copyFileSync(file.src, file.dest);
    console.log(`复制文件: ${file.src} -> ${file.dest}`);
}); 