-- Base de datos del ERP
-- Base de datos para el ERP Brasil

CREATE TABLE IF NOT EXISTS transacciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
        tipo VARCHAR(10) NOT NULL,
            descripcion VARCHAR(255) NOT NULL,
                monto DECIMAL(10, 2) NOT NULL,
                    fecha DATE NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS facturas (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                            descripcion VARCHAR(255) NOT NULL,
                                monto DECIMAL(10, 2) NOT NULL,
                                    fecha_vencimiento DATE NOT NULL,
                                        estado VARCHAR(20) DEFAULT 'Pendiente'
                                        );
                                        