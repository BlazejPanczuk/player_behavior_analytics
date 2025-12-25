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
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `id_user` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) DEFAULT NULL,
  `login` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `phone` char(9) DEFAULT NULL,
  `age` int DEFAULT NULL,
  `balance` decimal(10,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`id_user`)
) ENGINE=InnoDB AUTO_INCREMENT=119 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (1,'alex@example.com','Alex123','hashed_pw_1','12345678',25,0.00),(2,'bella@example.com','BellaR','hashed_pw_2','23456789',22,0.00),(3,'charlie@example.com','CharC','hashed_pw_3','34567890',28,0.00),(4,'dana@example.com','DanaX','hashed_pw_4','45678901',30,0.00),(5,'eric@example.com','Er1c','hashed_pw_5','56789012',19,0.00),(6,'fiona@example.com','FionaF','hashed_pw_6','67890123',27,0.00),(7,'george@example.com','Geo77','hashed_pw_7','78901234',24,0.00),(8,'hana@example.com','HanaL','hashed_pw_8','89012345',31,0.00),(9,'test','test','test','12345678',18,791.51),(10,NULL,'TestUser',NULL,NULL,NULL,89.06),(11,'Test@gmail.com','Qwer','qwer','987654321',21,175.01),(12,'plm','plm','plm','000000000',10,0.00),(13,'adrian.krawczyk@example.com','silver_wanderer','$2b$12$GK8d1a930cFakeHashADRIAN','512349876',27,0.00),(14,'kamil.piotrowski@example.com','nightfox','$2b$12$H81dL19FakeHashKAMIL','693112457',25,0.00),(15,'natalia.michalska@example.com','emberrose','$2b$12$ll91D93FakeHashNATALIA','578903412',23,0.00),(16,'bartlomiej.stepien@example.com','ironcrest','$2b$12$DD82aa92FakeHashBART','601748293',29,0.00),(101,'adam.kowalski@example.com','AdamK','Haslo123!','501882334',23,125.50),(102,'maria.nowak@example.com','MariaN','Qwerty987!','721443556',21,89.00),(103,'lukasz.wisniewski@example.com','LukiW','TestPass1!','609733821',25,300.00),(104,'katarzyna.zielinska@example.com','KasiaZ','Secure441!','734992110',22,45.75),(105,'patryk.wozniak@example.com','PatrykW','Pass5566!','512228903',24,0.00),(106,'monika.jankowska@example.com','MoniaJ','Janka2024!','795321440',28,210.20),(107,'karol.lewandowski@example.com','KarolL','Lewy446!','690543112',20,15.99),(108,'paulina.nowicka@example.com','PaulaN','N0wicKa!!','728944632',26,98.30),(109,'piotr.malicki@example.com','piotr.malicki','Haslo123!','500100200',25,0.00),(110,'anna.mazur@example.com','anna.mazur','Haslo123!','500100201',23,0.00),(111,'sebastian.krol@example.com','sebastian.krol','Haslo123!','500100202',28,0.00),(112,'dominika.walczak@example.com','dominika.walczak','Haslo123!','500100203',22,0.00),(113,'mateusz.kaczmarek@example.com','mateusz.kaczmarek','Haslo123!','500100204',27,0.00),(114,'julia.adamczyk@example.com','julia.adamczyk','Haslo123!','500100205',24,0.00),(115,'pawel.olszewski@example.com','pawel.olszewski','Haslo123!','500100206',29,0.00),(116,'weronika.stepien@example.com','weronika.stepien','Haslo123!','500100207',21,0.00),(117,'dariusz.sikora@example.com','dariusz.sikora','Haslo123!','500100208',31,0.00),(118,'olga.urbanska@example.com','olga.urbanska','Haslo123!','500100209',22,0.00);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
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
