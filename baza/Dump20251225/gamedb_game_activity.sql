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
-- Table structure for table `game_activity`
--

DROP TABLE IF EXISTS `game_activity`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `game_activity` (
  `id_game_activity` int NOT NULL AUTO_INCREMENT,
  `id_game` int DEFAULT NULL,
  `id_activity` int DEFAULT NULL,
  PRIMARY KEY (`id_game_activity`),
  KEY `id_game` (`id_game`),
  KEY `id_activity` (`id_activity`),
  CONSTRAINT `game_activity_ibfk_1` FOREIGN KEY (`id_game`) REFERENCES `game` (`id_game`),
  CONSTRAINT `game_activity_ibfk_2` FOREIGN KEY (`id_activity`) REFERENCES `activity` (`id_activity`)
) ENGINE=InnoDB AUTO_INCREMENT=89 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_activity`
--

LOCK TABLES `game_activity` WRITE;
/*!40000 ALTER TABLE `game_activity` DISABLE KEYS */;
INSERT INTO `game_activity` VALUES (1,1,1),(2,2,2),(3,3,3),(4,4,4),(5,5,5),(6,6,6),(7,7,7),(8,8,8),(9,9,9),(10,10,10),(11,11,11),(12,12,12),(13,13,13),(14,14,14),(15,15,15),(16,16,16),(17,17,17),(18,18,18),(19,19,19),(20,20,20),(21,21,21),(22,22,22),(23,23,23),(24,24,24),(25,25,25),(26,26,26),(27,27,27),(28,201,28),(29,202,29),(30,203,30),(31,204,31),(32,205,32),(33,206,33),(34,207,34),(35,208,35),(36,209,36),(37,210,37),(38,211,38),(39,212,39),(40,213,40),(41,214,41),(42,215,42),(43,216,43),(44,217,44),(45,218,45),(46,219,46),(47,220,47),(48,221,48),(49,1,28),(50,2,29),(51,3,30),(52,4,31),(53,5,32),(54,6,33),(55,7,34),(56,8,35),(57,9,36),(58,10,37),(59,11,38),(60,12,39),(61,13,40),(62,14,41),(63,15,42),(64,16,43),(65,17,44),(66,18,45),(67,19,46),(68,20,47),(69,21,48),(70,22,49),(71,23,50),(72,24,51),(73,25,52),(74,26,53),(75,27,54),(76,1,55),(77,2,56),(78,3,57),(79,4,58),(80,5,59),(81,6,60),(82,7,61),(83,8,62),(84,9,63),(85,10,64),(86,11,65),(87,12,66),(88,13,67);
/*!40000 ALTER TABLE `game_activity` ENABLE KEYS */;
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
