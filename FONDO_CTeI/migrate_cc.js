const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.resolve(__dirname, 'banco_app/banco.db');
const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error('Error connecting to database:', err.message);
        process.exit(1);
    }
    console.log('Connected to the SQLite database.');
});

db.serialize(() => {
    db.run('ALTER TABLE cuenta ADD COLUMN centro_costo TEXT', (err) => {
        if (err) {
            if (err.message.includes('duplicate column name')) {
                console.log('Column centro_costo already exists.');
            } else {
                console.error('Error adding column:', err.message);
            }
        } else {
            console.log('Column centro_costo added successfully.');
        }
        db.close();
    });
});
