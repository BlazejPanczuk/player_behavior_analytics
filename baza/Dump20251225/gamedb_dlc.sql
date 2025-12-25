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
-- Table structure for table `dlc`
--

DROP TABLE IF EXISTS `dlc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dlc` (
  `id_dlc` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `price` double DEFAULT NULL,
  `date_release` date DEFAULT NULL,
  `positive_rating` int DEFAULT NULL,
  `negative_rating` int DEFAULT NULL,
  PRIMARY KEY (`id_dlc`)
) ENGINE=InnoDB AUTO_INCREMENT=226 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dlc`
--

LOCK TABLES `dlc` WRITE;
/*!40000 ALTER TABLE `dlc` DISABLE KEYS */;
INSERT INTO `dlc` VALUES (1,'ARK: Scorched Earth',153,'2016-09-01',4137,1114),(2,'ARK: Aberration',153,'2017-12-12',NULL,NULL),(3,'ARK: Extinction',153,'2018-11-06',NULL,NULL),(4,'ARK: Valguero',0,'2016-05-17',NULL,NULL),(5,'ARK: Ragnarok',0,'2017-06-12',NULL,NULL),(6,'ARK: Genesis Season Pass',153,'2021-05-06',NULL,NULL),(7,'ARK: Scorched Earth Ascended',0,'2024-04-02',515,343),(8,'ARK: Aberration Ascended',0,'2024-09-05',1000,1143),(9,'ARK: The Center Ascended',0,'2024-06-05',441,589),(10,'ARK: Extinction Ascended',0,'2024-12-20',221,195),(11,'ESO: Blackwood',45,'2021-06-01',500,NULL),(12,'ESO: High Isle',45,'2022-06-06',269,NULL),(13,'ESO: Necrom',45,'2023-06-05',218,86),(14,'ESO: Morrowind',45,'2017-06-06',NULL,NULL),(15,'ESO: 2025 Content Pass',225,'2025-04-10',84,NULL),(16,'ESO: Plus Membership',22,'2016-11-02',843,NULL),(21,'Origins: The Hidden Ones',13.5,'2018-01-23',692,182),(22,'Origins: Curse of the Pharaohs',27,'2018-03-13',NULL,NULL),(23,'Origins: Season Pass',54,'2017-10-27',351,127),(24,'Origins: Deluxe Pack',45,'2025-04-06',238,106),(31,'Elden Ring: Shadow of the Erdtree',169,'2025-07-08',57523,23437),(41,'Skyrim: Dawnguard',90,'2012-08-02',1486,151),(42,'Skyrim: Hearthfire',90,'2012-09-04',1000,100),(43,'Skyrim: Dragonborn',90,'2012-12-04',1200,150),(51,'Sekiro: Digital Artwork & Mini Soundtrack',0,'2023-09-18',NULL,NULL),(71,'Battle Brothers: Beasts & Exploration',45,'2018-11-29',299,75),(72,'Battle Brothers: Blazing Deserts',45,'2020-08-13',312,81),(73,'Battle Brothers: Warriors of the North',45,'2019-05-09',150,30),(74,'Battle Brothers: Digital Lore & Art Book',22,NULL,NULL,NULL),(75,'Battle Brothers: Fangshire Helm',22,'2015-04-28',NULL,NULL),(81,'RDR2: Special Edition Content',160,NULL,NULL,NULL),(82,'RDR2: Ultimate Edition Content',200,NULL,NULL,NULL),(91,'Destiny 2 Season Pass (Seasons)',45,'2022-02-22',1200,300),(101,'No Man’s Sky: Doppelgänger Music Pack',18,'2021-08-11',NULL,NULL),(102,'No Man’s Sky: Pathfinder Armor Pack',9,'2021-09-18',NULL,NULL),(111,'Sun Haven: Celestial Pack',68,'2024-06-12',2,1),(112,'Sun Haven: Emerald Elegance Pack',68,'2024-08-03',1,0),(113,'Sun Haven: Squeaky Clean Pack',68,'2024-08-03',NULL,NULL),(114,'Sun Haven: Tis the Season Pack',0,'2025-03-15',19,5),(115,'Sun Haven: Pet Baby Tiger',0,'2021-06-13',NULL,NULL),(116,'Sun Haven: Gold Record Player',0,'2021-06-13',NULL,NULL),(121,'HoF2: Outlands and Outsiders',5.09,'2018-06-13',NULL,NULL),(122,'HoF2: The Servant and the Beast',5.09,'2018-10-15',16,5),(123,'HoF2: A Cold Hearth',4.39,'2018-12-12',8,NULL),(124,'HoF2: Official Soundtrack',35.99,'2017-11-07',NULL,NULL),(131,'Isaac: Afterbirth',49,'2015-10-30',7000,NULL),(132,'Isaac: Afterbirth+',45,'2017-03-15',NULL,NULL),(133,'Isaac: Repentance',56,'2021-03-31',NULL,NULL),(151,'God of Weapons: Gold Pack',15,NULL,NULL,NULL),(152,'God of Weapons: Platinum Pack',30,NULL,NULL,NULL),(161,'Dead by Daylight: Killer Pack 1',54,'2021-06-22',1100,320),(162,'Dead by Daylight: Survivor Pack 1',27,'2021-06-22',600,180),(163,'Dead by Daylight: Legacy of the Ghost Face',27,'2021-10-19',500,150),(171,'TW:WARHAMMER II Lizardmen Pack',72,'2017-06-27',4300,1200),(172,'TW:WARHAMMER II Tomb Kings Pack',72,'2017-10-10',3800,950),(173,'TW:WARHAMMER II Queen & Crone Pack',72,'2018-05-29',2600,700),(174,'TW:WARHAMMER II Warriors of Chaos Pack',72,'2018-12-13',4000,1100),(181,'BG3: Digital Deluxe Edition DLC',44,'2023-08-03',3680,320),(183,'DDLC Fan Pack',45,'2017-09-22',NULL,NULL),(184,'Ni no Kuni II: The Lair of the Lost Lord',40,'2018-12-13',NULL,NULL),(185,'Ni no Kuni II: The Tale of a Timeless Tome',55,'2019-03-19',NULL,NULL),(186,'Ni no Kuni II: Season Pass',36,'2018-07-10',NULL,NULL),(187,'Ni no Kuni II: Adventure Pack',0,'2018-08-09',NULL,NULL),(191,'RimWorld: Royalty',27,NULL,NULL,NULL),(192,'RimWorld: Ideology',27,NULL,NULL,NULL),(193,'RimWorld: Biotech',27,NULL,NULL,NULL),(201,'Witcher 3: Hearts of Stone',45,'2015-10-13',NULL,NULL),(202,'Witcher 3: Blood and Wine',68,'2016-05-31',NULL,NULL),(203,'Witcher 3: GOTY Bundle',136,NULL,NULL,NULL),(204,'Ashes of Ariandel',14.99,'2016-10-25',86,14),(205,'The Ringed City',14.99,'2017-03-28',92,8),(206,'Going East!',9.99,'2013-09-20',91,9),(207,'Scandinavia',17.99,'2015-05-06',93,7),(208,'Vive La France!',17.99,'2016-12-05',94,6),(209,'Italia',17.99,'2017-12-05',94,6),(210,'Beyond the Baltic Sea',17.99,'2018-11-29',92,8),(211,'Phantom Liberty',29.99,'2023-09-26',94,6),(212,'Cyberpunk 2077 Cosmetic Pack',0,'2021-08-18',85,15),(213,'Dark Future Pack',6.99,'2020-06-04',89,11),(214,'MegaCorp Pack',6.99,'2020-06-04',91,9),(215,'Rival Tech Pack',6.99,'2022-05-05',93,7),(216,'Iceborne',39.99,'2019-01-09',96,4),(217,'The Committed',6.99,'2021-10-27',89,11),(218,'The Prodigal Daughter',6.99,'2020-01-15',92,8),(219,'Spirit of Nian',6.99,'2021-02-10',90,10),(220,'The War Across the Sand',5.99,'2022-04-15',87,13),(221,'Art of War',19.99,'2014-10-30',95,5),(222,'Rights of Man',19.99,'2016-10-11',92,8),(223,'Common Sense',14.99,'2015-06-09',74,26),(224,'Mandate of Heaven',19.99,'2017-04-06',61,39),(225,'Leviathan',19.99,'2021-04-27',20,80);
/*!40000 ALTER TABLE `dlc` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-25 20:48:43
