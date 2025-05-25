-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               8.0.32 - MySQL Community Server - GPL
-- Server OS:                    Win64
-- HeidiSQL Version:             12.7.0.6850
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Dumping database structure for moex_db
CREATE DATABASE IF NOT EXISTS `moex_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `moex_db`;

-- Dumping structure for table moex_db.boardgroups
CREATE TABLE IF NOT EXISTS `boardgroups` (
  `id` int unsigned NOT NULL,
  `trade_engine_id` int DEFAULT NULL,
  `trade_engine_name` varchar(45) DEFAULT NULL,
  `trade_engine_title` varchar(765) DEFAULT NULL,
  `market_id` int DEFAULT NULL,
  `market_name` varchar(45) DEFAULT NULL,
  `name` varchar(192) NOT NULL DEFAULT '',
  `title` varchar(765) DEFAULT NULL,
  `is_default` int DEFAULT NULL,
  `board_group_id` int DEFAULT NULL,
  `is_traded` int DEFAULT NULL,
  `is_order_driven` int DEFAULT NULL,
  `category` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table moex_db.boards
CREATE TABLE IF NOT EXISTS `boards` (
  `id` int unsigned NOT NULL,
  `board_group_id` int DEFAULT NULL,
  `engine_id` int DEFAULT NULL,
  `market_id` int DEFAULT NULL,
  `boardid` varchar(12) NOT NULL DEFAULT '',
  `board_title` varchar(381) DEFAULT NULL,
  `is_traded` int DEFAULT NULL,
  `has_candles` int DEFAULT NULL,
  `is_primary` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `boardid` (`boardid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table moex_db.durations
CREATE TABLE IF NOT EXISTS `durations` (
  `interval` int NOT NULL,
  `duration` int DEFAULT NULL,
  `days` int DEFAULT NULL,
  `title` varchar(765) DEFAULT '',
  `hint` varchar(765) DEFAULT '',
  PRIMARY KEY (`interval`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table moex_db.engines
CREATE TABLE IF NOT EXISTS `engines` (
  `id` int unsigned NOT NULL,
  `name` varchar(45) NOT NULL DEFAULT '',
  `title` varchar(765) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table moex_db.last_arrival
CREATE TABLE IF NOT EXISTS `last_arrival` (
  `id` bigint NOT NULL,
  `secid` varchar(51) NOT NULL,
  `shortname` varchar(189) DEFAULT NULL,
  `regnumber` varchar(189) DEFAULT NULL,
  `name` varchar(765) DEFAULT NULL,
  `isin` varchar(51) DEFAULT NULL,
  `is_traded` int DEFAULT NULL,
  `emitent_id` int DEFAULT NULL,
  `emitent_title` varchar(765) DEFAULT NULL,
  `emitent_inn` varchar(30) DEFAULT NULL,
  `emitent_okpo` varchar(24) DEFAULT NULL,
  `gosreg` varchar(189) DEFAULT NULL,
  `type` varchar(93) DEFAULT NULL,
  `group` varchar(93) DEFAULT NULL,
  `primary_boardid` varchar(12) DEFAULT NULL,
  `marketprice_boardid` varchar(12) DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `secid` (`secid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- Data exporting was unselected.

-- Dumping structure for table moex_db.main_table
CREATE TABLE IF NOT EXISTS `main_table` (
  `id` bigint NOT NULL,
  `secid` varchar(51) NOT NULL,
  `shortname` varchar(189) DEFAULT NULL,
  `regnumber` varchar(189) DEFAULT NULL,
  `name` varchar(765) DEFAULT NULL,
  `isin` varchar(51) DEFAULT NULL,
  `is_traded` int DEFAULT NULL,
  `emitent_id` int DEFAULT NULL,
  `emitent_title` varchar(765) DEFAULT NULL,
  `emitent_inn` varchar(30) DEFAULT NULL,
  `emitent_okpo` varchar(24) DEFAULT NULL,
  `gosreg` varchar(189) DEFAULT NULL,
  `type` varchar(93) DEFAULT NULL,
  `group` varchar(93) DEFAULT NULL,
  `primary_boardid` varchar(12) DEFAULT NULL,
  `marketprice_boardid` varchar(12) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `secid` (`secid`),
  FULLTEXT KEY `shortname` (`shortname`),
  FULLTEXT KEY `name` (`name`),
  FULLTEXT KEY `emitent_title` (`emitent_title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

-- Data exporting was unselected.

-- Dumping structure for table moex_db.main_table_search
CREATE TABLE IF NOT EXISTS `main_table_search` (
  `id` bigint NOT NULL,
  `secid` varchar(51) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `shortname` varchar(189) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` varchar(765) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_traded` int DEFAULT NULL,
  `type` varchar(93) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `group` varchar(93) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `primary_boardid` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `trade_engine_name` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `market_name` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `mask` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Data exporting was unselected.

-- Dumping structure for table moex_db.markets
CREATE TABLE IF NOT EXISTS `markets` (
  `id` int unsigned NOT NULL,
  `trade_engine_id` int NOT NULL,
  `trade_engine_name` varchar(45) NOT NULL DEFAULT '',
  `trade_engine_title` varchar(765) NOT NULL DEFAULT '',
  `market_name` varchar(45) NOT NULL DEFAULT '',
  `market_title` varchar(765) DEFAULT NULL,
  `market_id` int DEFAULT NULL,
  `marketplace` varchar(48) DEFAULT NULL,
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

-- Data exporting was unselected.

-- Dumping structure for table moex_db.securitycollections
CREATE TABLE IF NOT EXISTS `securitycollections` (
  `id` int unsigned NOT NULL,
  `name` varchar(96) NOT NULL DEFAULT '',
  `title` varchar(765) DEFAULT NULL,
  `security_group_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table moex_db.securitygroups
CREATE TABLE IF NOT EXISTS `securitygroups` (
  `id` int unsigned NOT NULL,
  `name` varchar(93) NOT NULL DEFAULT '',
  `title` varchar(765) DEFAULT NULL,
  `is_hidden` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.

-- Dumping structure for table moex_db.securitytypes
CREATE TABLE IF NOT EXISTS `securitytypes` (
  `id` int unsigned NOT NULL,
  `trade_engine_id` int DEFAULT NULL,
  `trade_engine_name` varchar(45) DEFAULT NULL,
  `trade_engine_title` varchar(765) DEFAULT NULL,
  `security_type_name` varchar(93) NOT NULL DEFAULT '',
  `security_type_title` varchar(765) DEFAULT NULL,
  `security_group_name` varchar(93) DEFAULT NULL,
  `stock_type` varchar(3) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `security_type_name` (`security_type_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data exporting was unselected.


/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
