-- moex_db.boardgroups определение

CREATE TABLE `boardgroups` (
  `id` int unsigned NOT NULL,
  `trade_engine_id` int DEFAULT NULL,
  `trade_engine_name` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `trade_engine_title` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `market_id` int DEFAULT NULL,
  `market_name` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(192) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `title` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_default` int DEFAULT NULL,
  `board_group_id` int DEFAULT NULL,
  `is_traded` int DEFAULT NULL,
  `is_order_driven` int DEFAULT NULL,
  `category` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- moex_db.boards определение

CREATE TABLE `boards` (
  `id` int unsigned NOT NULL,
  `board_group_id` int DEFAULT NULL,
  `engine_id` int DEFAULT NULL,
  `market_id` int DEFAULT NULL,
  `boardid` varchar(12) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `board_title` varchar(381) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_traded` int DEFAULT NULL,
  `has_candles` int DEFAULT NULL,
  `is_primary` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `boardid` (`boardid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- moex_db.durations определение

CREATE TABLE `durations` (
  `interval` int NOT NULL,
  `duration` int DEFAULT NULL,
  `days` int DEFAULT NULL,
  `title` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `hint` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT '',
  PRIMARY KEY (`interval`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- moex_db.engines определение

CREATE TABLE `engines` (
  `id` int unsigned NOT NULL,
  `name` varchar(45) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `title` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- moex_db.last_arrival определение

CREATE TABLE `last_arrival` (
  `id` bigint NOT NULL,
  `secid` varchar(51) COLLATE utf8mb4_unicode_ci NOT NULL,
  `shortname` varchar(189) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `regnumber` varchar(189) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `isin` varchar(51) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_traded` int DEFAULT NULL,
  `emitent_id` int DEFAULT NULL,
  `emitent_title` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `emitent_inn` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `emitent_okpo` varchar(24) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `gosreg` varchar(189) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `type` varchar(93) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `group` varchar(93) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `primary_boardid` varchar(12) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `marketprice_boardid` varchar(12) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `secid` (`secid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;


-- moex_db.main_table определение

CREATE TABLE `main_table` (
  `id` bigint NOT NULL,
  `secid` varchar(51) COLLATE utf8mb4_unicode_ci NOT NULL,
  `shortname` varchar(189) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `regnumber` varchar(189) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `isin` varchar(51) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_traded` int DEFAULT NULL,
  `emitent_id` int DEFAULT NULL,
  `emitent_title` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `emitent_inn` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `emitent_okpo` varchar(24) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `gosreg` varchar(189) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `type` varchar(93) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `group` varchar(93) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `primary_boardid` varchar(12) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `marketprice_boardid` varchar(12) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `secid` (`secid`),
  FULLTEXT KEY `shortname` (`shortname`),
  FULLTEXT KEY `name` (`name`),
  FULLTEXT KEY `emitent_title` (`emitent_title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;


-- moex_db.main_table_search определение

CREATE TABLE `main_table_search` (
  `id` bigint NOT NULL,
  `secid` varchar(51) COLLATE utf8mb4_unicode_ci NOT NULL,
  `shortname` varchar(189) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_traded` int DEFAULT NULL,
  `type` varchar(93) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `group` varchar(93) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `primary_boardid` varchar(12) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `trade_engine_name` varchar(45) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `market_name` varchar(45) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `mask` text COLLATE utf8mb4_unicode_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- moex_db.markets определение

CREATE TABLE `markets` (
  `id` int unsigned NOT NULL,
  `trade_engine_id` int NOT NULL,
  `trade_engine_name` varchar(45) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `trade_engine_title` varchar(765) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `market_name` varchar(45) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `market_title` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `market_id` int DEFAULT NULL,
  `marketplace` varchar(48) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_otc` int DEFAULT NULL,
  `has_history_files` int DEFAULT NULL,
  `has_history_trades_files` int DEFAULT NULL,
  `has_trades` int DEFAULT NULL,
  `has_history` int DEFAULT NULL,
  `has_candles` int DEFAULT NULL,
  `has_orderbook` int DEFAULT NULL,
  `has_tradingsession` int DEFAULT NULL,
  `has_extra_yields` int DEFAULT NULL,
  `has_delay` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- moex_db.securitycollections определение

CREATE TABLE `securitycollections` (
  `id` int unsigned NOT NULL,
  `name` varchar(96) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `title` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `security_group_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- moex_db.securitygroups определение

CREATE TABLE `securitygroups` (
  `id` int unsigned NOT NULL,
  `name` varchar(93) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `title` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_hidden` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- moex_db.securitytypes определение

CREATE TABLE `securitytypes` (
  `id` int unsigned NOT NULL,
  `trade_engine_id` int DEFAULT NULL,
  `trade_engine_name` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `trade_engine_title` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `security_type_name` varchar(93) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `security_type_title` varchar(765) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `security_group_name` varchar(93) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `stock_type` varchar(3) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `security_type_name` (`security_type_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;