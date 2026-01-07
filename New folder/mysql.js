const mysql = require('mysql2');
const connection = mysql.createConnection({
  host: 'localhost',
  user: 'myappuser',
  password: 'StrongPassword123!',
  database: 'myappdb'
});
connection.connect(err => {
  if (err) throw err;
  console.log('Connected to MySQL!');
});