create table users( id integer primary key AUTOINCREMENT, name text not null,
                password text not null,
                admin boolean not null DEFAULT '0');


create table employees ( employeeId integer primary key AUTOINCREMENT,
                name text not null, 
                email text, 
                phone integer, 
                address text, 
                joining_date timestamp DEFAULT CURRENT_TIMESTAMP);


create table operations( operationId integer primary key AUTOINCREMENT,
                name text not null, 
                duration text, 
                start_date timestamp DEFAULT CURRENT_TIMESTAMP,
                employeeName text,
                operationType text);