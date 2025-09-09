CREATE TABLE Rol (
    id_rol SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE  
);
insert into Rol (nombre) values ('Administrador'),('Vendedor'),('Comprador');
select * from rol
create table Usuario(
	id_usuario SERIAL primary key,
	nombre varchar(100) not null,
	correo varchar(100) not null unique,
	password varchar(255) not null,
	telefono varchar(20),
	id_rol int not null,
	estado boolean default true,
	foreign key (id_rol) references Rol(id_rol)
);

create table Categoria(
	id_categoria serial primary key,
	nombre varchar(50) not null unique
);
insert into Categoria (nombre) values ('Dulces'), ('Accesorios Hombre'), ('Accesorios Mujer'), ('tenis')

create table Producto (
	id_producto serial primary key,
	nombre varchar(100) not null,
	descripcion text,
	precio decimal (10,2) not null,
	stock int not null,
	id_categoria int not null,
	id_vendedor int not null,
	estado boolean default true,
	foreign key (id_categoria) references Categoria(id_categoria),
	Foreign key (id_vendedor) references Usuario(id_usuario)
);

create table Pedido (
id_pedido serial primary key,
id_comprador int not null,
fecha timestamp default current_timestamp,
total decimal (10,2) not null,
estado varchar(20) default 'Pendiente',
Foreign key (id_comprador) references Usuario(id_usuario)
);

create table DetallePedido (
	id_detalle serial primary key,
	id_pedido int not null,
	id_producto int not null,
	cantidad int not null,
	precio_unitario decimal (10,2) not null,
	subtotal decimal (10,2) not null,
	foreign key (id_pedido) references Pedido(id_pedido),
	foreign key (id_producto) references Producto(id_producto)
	
);

select * from Usuario