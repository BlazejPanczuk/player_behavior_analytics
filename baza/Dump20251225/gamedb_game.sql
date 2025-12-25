-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: localhost    Database: gamedb
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `game`
--

DROP TABLE IF EXISTS `game`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game` (
  `id_game` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `price` double DEFAULT NULL,
  `positive_rating` int DEFAULT NULL,
  `negative_rating` int DEFAULT NULL,
  `last_update` date DEFAULT NULL,
  `release_date` date DEFAULT NULL,
  `image_url` varchar(500) DEFAULT NULL,
  `mods` int DEFAULT NULL,
  `copies_sold` bigint DEFAULT NULL,
  `current_players` int DEFAULT NULL,
  `peak_players` int DEFAULT NULL,
  `creator` varchar(40) DEFAULT NULL,
  `steam_appid` int DEFAULT NULL,
  `peak_24h_players` int DEFAULT NULL,
  PRIMARY KEY (`id_game`)
) ENGINE=InnoDB AUTO_INCREMENT=222 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game`
--

LOCK TABLES `game` WRITE;
/*!40000 ALTER TABLE `game` DISABLE KEYS */;
INSERT INTO `game` VALUES (1,'ARK Survival Evolved',67.99,618337,118588,'2025-07-11','2017-10-29','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/1.jpg',25235,76000000,30949,247292,'Studio Wildcard',346110,32244),(2,'ARK: Survival Ascended',208.49,47612,33490,'2025-07-11','2023-10-25','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/2.jpg',0,1600000,38061,98047,'Studio Wildcard',2399830,38364),(3,'Amnesia: The Dark Descent',91.99,32378,1853,'2025-07-10','2010-09-08','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/3.jpg',317,1400000,102,5566,'Frictional Games',57300,124),(4,'Assassin\'s Creed Origins',249.9,98040,16316,'2025-07-08','2017-10-27','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/4.jpg',0,10000000,7450,41541,'Ubisoft Montreal',582160,8036),(5,'Baldur\'s Gate 3',249,744536,24261,'2025-07-10','2023-08-03','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/5.jpg',0,20000000,75779,875343,'Larian Studios',1086940,80303),(6,'Battle Brothers',99.99,21628,2923,'2025-07-06','2017-03-24','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/6.jpg',0,1040000,1928,8055,'Overhype Studios',365360,1928),(7,'Counter-Strike 2',0,7694796,1189249,'2025-07-07','2023-09-27','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/7.jpg',0,95000000,1487771,1818368,'Valve',730,1603583),(8,'Dead by Daylight',71.99,811000,220000,'2025-07-09','2016-06-14','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/8.jpg',0,60000000,53189,120430,'Behaviour Interactive',381210,54229),(9,'Destiny 2',0,627000,168000,'2025-07-11','2019-10-01','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/9.jpg',0,55000000,29899,316651,'Bungie',1085660,37479),(10,'Doki Doki Literature Club!',0,201000,7497,'2025-07-11','2017-09-22','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/10.jpg',0,2000000,649,7402,'Team Salvato',698780,771),(11,'Elden Ring',249,993223,75899,'2025-07-11','2022-02-24','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/11.jpg',0,15500000,45003,952523,'FromSoftware',1245620,46898),(12,'The Elder Scrolls Online',79.9,124242,30182,'2025-07-10','2014-04-04','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/12.jpg',0,15000000,11528,49061,'ZeniMax Online Studios',306130,12496),(13,'God of Weapons',24.99,3646,644,'2025-06-30','2023-09-12','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/13.jpg',0,50000,284,284,'Archmage Labs',2487510,NULL),(14,'Gothic II: Gold Edition',91.99,14632,993,'2025-07-08','2005-11-29','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/14.jpg',455,750000,2028,2679,'Piranha Bytes',39510,2028),(15,'Hand of Fate 2',107.99,4786,884,'2025-05-16','2017-11-07','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/15.jpg',35,474100,120,6036,'Defiant Development',614570,140),(16,'Ni no Kuni II: Revenant Kingdom',259.99,9045,1742,'2025-07-10','2018-03-23','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/16.jpg',2,900000,91,10708,'Level-5 Inc.',589360,103),(17,'No Man’s Sky',274.99,296478,59646,'2025-07-09','2016-08-12','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/17.jpg',0,12500000,20871,212321,'Hello Games',275850,20871),(18,'Oxygen Not Included',89.99,126125,4231,'2025-07-11','2019-07-30','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/18.jpg',0,5700000,17175,27380,'Klei Entertainment',457140,18265),(19,'Red Dead Redemption 2',62.47,690474,61887,'2025-07-09','2019-12-05','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/19.jpg',0,16060000,52681,99759,'Rockstar Games',1174180,54705),(20,'RimWorld',139.99,66561,3288,'2025-07-11','2018-10-17','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/20.jpg',43872,9000000,31771,95851,'Ludeon Studios',294100,31918),(21,'Robocraft',0,86208,31811,'2025-07-14','2017-08-24','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/21.png',0,10000000,7,26598,'Freejam',301520,7),(22,'Sekiro: Shadows Die Twice',254,311057,15470,'2025-07-11','2019-03-22','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/22.jpg',0,10000000,7342,124334,'FromSoftware',814380,8262),(23,'Sun Haven',114.99,29600,9000,'2025-07-11','2023-03-10','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/23.jpg',0,500000,2004,12688,'Pixel Sprout Studios',1432860,2234),(24,'The Binding of Isaac: Rebirth',53.99,338579,9469,'2025-07-11','2014-11-04','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/24.jpg',0,8000000,26313,70483,'Nicalis, Inc.',250900,26588),(25,'The Elder Scrolls V: Skyrim',67.99,313165,26986,'2025-07-11','2011-11-11','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/25.jpg',24488,60000000,2007,90780,'Bethesda Game Studios',72850,2058),(26,'The Witcher 3: Wild Hunt',99.99,840000,40000,'2025-07-11','2015-05-19','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/26.jpg',0,14140000,32600,103329,'CD PROJEKT RED',292030,32872),(27,'Total War: WARHAMMER II',63.74,114891,9501,'2025-07-11','2017-09-28','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/27.jpg',12738,2900000,2060,84254,'Creative Assembly',594570,2091),(201,'Hollow Knight',54.99,247000,6000,'2024-06-03','2017-02-24','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/201.jpg',120,3000000,18854,95428,'Team Cherry',367520,19052),(202,'Subnautica',112.99,220000,14000,'2023-07-21','2018-01-23','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/202.jpg',350,6000000,8752,50876,'Unknown Worlds',264710,8752),(203,'Hades',107.99,200000,5000,'2024-05-14','2020-09-17','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/203.jpg',80,4000000,9274,54015,'Supergiant Games',1145360,9291),(204,'Stardew Valley',39.99,590000,9000,'2024-09-11','2016-02-26','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/204.jpg',12000,30000000,109581,236614,'ConcernedApe',413150,122677),(205,'Dark Souls III',239,320000,25000,'2024-01-19','2016-04-11','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/205.jpg',500,10000000,6707,129831,'FromSoftware',374320,6883),(206,'Terraria',36.99,950000,25000,'2023-12-29','2011-05-16','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/206.jpg',25000,45000000,43214,486918,'Re-Logic',105600,45540),(207,'Euro Truck Simulator 2',89.99,480000,35000,'2024-03-04','2012-10-18','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/207.jpg',1500,13000000,64911,72523,'SCS Software',227300,64911),(208,'Cyberpunk 2077',249,570000,110000,'2024-09-02','2020-12-10','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/208.jpg',300,30000000,55963,830387,'CD Projekt RED',1091500,56669),(209,'Path of Exile',0,190000,14000,'2024-05-05','2013-10-23','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/209.jpg',1800,10000000,11974,228398,'Grinding Gear Games',238960,12901),(210,'Deep Rock Galactic',127.99,215000,5000,'2024-08-09','2020-05-13','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/210.jpg',1100,7000000,15963,53558,'Ghost Ship Games',548430,17198),(211,'Slay the Spire',89.99,230000,8000,'2024-04-18','2019-01-23','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/211.jpg',450,3000000,45279,48385,'Mega Crit',646570,48385),(212,'Factorio',142.99,145000,2000,'2024-03-12','2020-08-14','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/212.jpg',2500,3500000,21155,118166,'Wube Software',427520,21942),(213,'Monster Hunter: World',249,350000,24000,'2024-02-26','2018-08-09','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/213.jpg',120,24000000,24271,329333,'Capcom',582010,27496),(214,'Kenshi',107.99,52000,6000,'2024-04-28','2018-12-06','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/214.jpg',1100,1000000,6504,11572,'Lo-Fi Games',233860,6504),(215,'Hunt: Showdown',169,145000,21000,'2024-08-30','2019-08-27','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/215.png',300,5000000,32202,59968,'Crytek',594650,36023),(216,'Baldur\'s Gate II: Enhanced Edition',39.99,21000,1500,'2025-12-10','2013-11-15','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/216.jpg',0,2000000,560,2644,'Beamdog',257350,560),(217,'Baldur\'s Gate: Enhanced Edition',39.99,18000,1800,'2025-12-10','2012-11-28','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/217.jpg',0,2500000,722,3756,'Beamdog',228280,793),(218,'Sands of Salzaar',49.99,8300,1100,'2025-12-10','2021-01-22','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/218.jpg',0,500000,142,21047,'Han-Squirrel',1094520,149),(219,'Europa Universalis IV',149.99,110000,30000,'2025-12-10','2013-08-13','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/219.jpg',0,3000000,10684,47844,'Paradox',236850,10684),(220,'Tiny Rogues',39.99,15000,700,'2025-12-10','2022-10-14','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/220.jpg',0,500000,NULL,NULL,'RubyDev',2075020,NULL),(221,'Lethal Company',19.99,260000,6000,'2025-12-10','2023-10-24','C:/Users/blaze/Desktop/Aplikacja/__inz_assets_f3a9c1e7b2/221.jpg',0,12000000,6147,239369,'Zeekerss',1966720,7116);
/*!40000 ALTER TABLE `game` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-25 20:48:44
