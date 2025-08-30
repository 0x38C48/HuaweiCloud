USE home_manager;

CREATE TABLE IF NOT EXISTS user_home_data (
    id INT AUTO_INCREMENT COMMENT '主键ID',
    user_id INT NOT NULL COMMENT '用户唯一标识',
    data_date DATE NOT NULL COMMENT '数据所属日期（格式：YYYY-MM-DD）',
    home_status JSON NOT NULL COMMENT '家居状态数据（JSON格式，{"老人":"有/无","小孩":"有/无"）',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间（修改时自动更新）',
    UNIQUE KEY uk_user_date (user_id, data_date),
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户家居状态数据表';