"""Kafka service for recipe event streaming."""

import json
import os
from typing import Dict, Any, Optional, Callable
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class KafkaService:
    """Service for producing and consuming recipe events via Kafka."""
    
    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        topic: Optional[str] = None
    ):
        """
        Initialize Kafka service.
        
        Args:
            bootstrap_servers: Kafka bootstrap servers (default: from env)
            topic: Default topic name (default: from env)
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            'KAFKA_BOOTSTRAP_SERVERS',
            'localhost:9092'
        )
        self.topic = topic or os.getenv('KAFKA_TOPIC_RECIPES', 'reddit-recipes')
        self.producer: Optional[KafkaProducer] = None
        self.consumer: Optional[KafkaConsumer] = None
    
    def get_producer(self) -> KafkaProducer:
        """Get or create a Kafka producer."""
        if self.producer is None or self.producer._closed:
            # Create new producer if none exists or if it was closed
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                max_in_flight_requests_per_connection=1
            )
        return self.producer
    
    def get_consumer(
        self,
        group_id: Optional[str] = None,
        auto_offset_reset: str = 'earliest'
    ) -> KafkaConsumer:
        """
        Get or create a Kafka consumer.
        
        Args:
            group_id: Consumer group ID (default: from env)
            auto_offset_reset: Where to start reading ('earliest' or 'latest')
            
        Returns:
            KafkaConsumer instance
        """
        if self.consumer is None:
            consumer_group = group_id or os.getenv(
                'KAFKA_CONSUMER_GROUP',
                'recipe-processors'
            )
            
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                group_id=consumer_group,
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=True,
                max_poll_records=10
            )
        return self.consumer
    
    def publish_recipe(
        self,
        recipe_data: Dict[str, Any],
        key: Optional[str] = None,
        topic: Optional[str] = None
    ) -> bool:
        """
        Publish a recipe event to Kafka.
        
        Args:
            recipe_data: Recipe data dictionary
            key: Optional message key (e.g., recipe ID)
            topic: Topic to publish to (default: self.topic)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            producer = self.get_producer()
            target_topic = topic or self.topic
            
            # Add metadata
            message = {
                **recipe_data,
                '_kafka_metadata': {
                    'source': 'reddit-scraper',
                    'version': '1.0'
                }
            }
            
            # Send message
            future = producer.send(
                target_topic,
                value=message,
                key=key
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            
            print(f"✅ Published to Kafka: {target_topic} "
                  f"(partition={record_metadata.partition}, "
                  f"offset={record_metadata.offset})")
            
            return True
            
        except KafkaError as e:
            print(f"❌ Kafka error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error publishing to Kafka: {e}")
            return False
    
    def consume_recipes(
        self,
        callback: Callable[[Dict[str, Any]], None],
        group_id: Optional[str] = None,
        max_messages: Optional[int] = None
    ):
        """
        Consume recipe events from Kafka.
        
        Args:
            callback: Function to call for each message
            group_id: Consumer group ID
            max_messages: Max number of messages to consume (None = infinite)
        """
        try:
            consumer = self.get_consumer(group_id=group_id)
            
            print(f"🔄 Consuming from Kafka topic: {self.topic}")
            print(f"📡 Bootstrap servers: {self.bootstrap_servers}")
            print(f"👥 Consumer group: {group_id or os.getenv('KAFKA_CONSUMER_GROUP')}")
            print("\nWaiting for messages... (Press Ctrl+C to stop)\n")
            
            message_count = 0
            
            for message in consumer:
                try:
                    recipe_data = message.value
                    
                    # Call the callback function
                    callback(recipe_data)
                    
                    message_count += 1
                    
                    # Check if we've reached max messages
                    if max_messages and message_count >= max_messages:
                        print(f"\n✅ Processed {message_count} messages")
                        break
                        
                except Exception as e:
                    print(f"⚠️  Error processing message: {e}")
                    continue
                    
        except KeyboardInterrupt:
            print(f"\n\n⛔ Stopped consuming. Processed {message_count} messages")
        finally:
            if self.consumer:
                self.consumer.close()
                print("✅ Closed Kafka consumer")
    
    def close(self):
        """Close Kafka connections."""
        if self.producer and not self.producer._closed:
            self.producer.flush()
            self.producer.close()
            self.producer = None  # Clear reference after closing
            print("✅ Closed Kafka producer")
        
        if self.consumer:
            self.consumer.close()
            self.consumer = None  # Clear reference after closing
            print("✅ Closed Kafka consumer")
    
    def health_check(self) -> bool:
        """Check if Kafka is accessible."""
        try:
            producer = self.get_producer()
            # Try to fetch metadata
            producer.bootstrap_connected()
            return True
        except Exception as e:
            print(f"❌ Kafka health check failed: {e}")
            return False


def get_kafka_service(
    bootstrap_servers: Optional[str] = None,
    topic: Optional[str] = None
) -> KafkaService:
    """
    Get or create Kafka service instance.
    
    Note: Creates a new instance each time to avoid shared state issues
    in Temporal workflows where activities run in different contexts.
    """
    return KafkaService(
        bootstrap_servers=bootstrap_servers,
        topic=topic
    )

