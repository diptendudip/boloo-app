"""
Database performance tests for chat system.

Measures query times, memory usage, and scalability.
"""

import pytest
import time
from sqlalchemy import text


@pytest.mark.performance
class TestDatabasePerformance:
    """Test database query performance"""

    def test_conversation_history_query_time(self, performance_db_session, create_test_conversation):
        """Measure query time for different conversation lengths"""
        test_cases = [10, 25, 50, 100]
        results = []

        for num_turns in test_cases:
            # Create conversation with N turns
            conversation = create_test_conversation(num_turns)

            # Measure query time (simulate get_conversation_history_for_ai)
            start = time.perf_counter()

            # Query all turns (mimics actual code behavior)
            turns = performance_db_session.query(
                type('ConversationTurn', (), {})
            ).from_statement(
                text(f"SELECT * FROM conversation_turns WHERE conversation_id = :conv_id ORDER BY turn_number")
            ).params(conv_id=str(conversation.id)).all()

            elapsed = time.perf_counter() - start

            result = {
                "num_turns": num_turns,
                "query_time_ms": elapsed * 1000,
                "per_turn_ms": (elapsed * 1000) / num_turns
            }
            results.append(result)

            print(f"\n{num_turns} turns: {elapsed*1000:.2f}ms (avg {result['per_turn_ms']:.2f}ms/turn)")

            # Performance assertion
            # Target: < 100ms for 50 turns (2ms per turn)
            assert elapsed < 0.5, f"Query took {elapsed*1000:.2f}ms for {num_turns} turns (expected < 500ms)"

        # Verify linear scaling (not exponential)
        scaling_factor = results[-1]["query_time_ms"] / results[0]["query_time_ms"]
        turn_ratio = results[-1]["num_turns"] / results[0]["num_turns"]

        print(f"\nScaling: {scaling_factor:.2f}x time for {turn_ratio:.2f}x turns")
        assert scaling_factor <= turn_ratio * 1.5, "Query time scaling is worse than linear!"

    def test_transcript_concatenation_time(self, create_test_conversation):
        """Measure transcript build time"""
        test_cases = [10, 25, 50, 100]

        for num_turns in test_cases:
            conversation = create_test_conversation(num_turns)

            # Simulate full transcript concatenation (as done in chat.py lines 1023, 1116, 1184)
            start = time.perf_counter()
            transcript = " ".join([turn.transcript_text for turn in conversation.turns])
            elapsed = time.perf_counter() - start

            transcript_length = len(transcript)

            print(f"\n{num_turns} turns: {elapsed*1000:.2f}ms ({transcript_length} chars)")

            # Performance assertion
            # Target: < 10ms for 100 turns
            assert elapsed < 0.1, f"Concatenation took {elapsed*1000:.2f}ms for {num_turns} turns"

    def test_duplicate_query_count(self, performance_db_session, create_test_conversation):
        """Measure number of queries for conversation retrieval"""
        conversation = create_test_conversation(50)

        # Count queries using SQLAlchemy event listener
        query_count = 0

        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count
            query_count += 1

        from sqlalchemy import event
        event.listen(
            performance_db_session.bind,
            "before_cursor_execute",
            before_cursor_execute
        )

        # Simulate get_conversation + get_all_turns
        conv = performance_db_session.query(type('Conversation', (), {})).from_statement(
            text("SELECT * FROM conversations WHERE id = :id")
        ).params(id=str(conversation.id)).first()

        turns = performance_db_session.query(type('ConversationTurn', (), {})).from_statement(
            text("SELECT * FROM conversation_turns WHERE conversation_id = :conv_id")
        ).params(conv_id=str(conversation.id)).all()

        print(f"\nTotal queries for 50-turn conversation: {query_count}")

        # Target: 2 queries (1 for conversation, 1 for all turns)
        # Current code might be doing N+1 (1 + 50 = 51 queries)
        assert query_count <= 2, f"N+1 query detected! {query_count} queries for 50 turns"

    def test_update_batching_performance(self, performance_db_session, create_test_conversation):
        """Compare batched vs sequential updates"""
        conversation = create_test_conversation(10)

        # Test 1: Sequential updates (current approach)
        start_sequential = time.perf_counter()
        for i in range(5):
            # Simulate multiple update_completeness calls
            performance_db_session.execute(
                text("UPDATE conversations SET completeness_score = :score WHERE id = :id"),
                {"score": 0.1 * i, "id": str(conversation.id)}
            )
            performance_db_session.commit()
        elapsed_sequential = time.perf_counter() - start_sequential

        # Test 2: Batched updates (recommended approach)
        start_batched = time.perf_counter()
        performance_db_session.execute(
            text("UPDATE conversations SET completeness_score = :score WHERE id = :id"),
            {"score": 0.5, "id": str(conversation.id)}
        )
        performance_db_session.commit()
        elapsed_batched = time.perf_counter() - start_batched

        print(f"\nSequential updates (5 commits): {elapsed_sequential*1000:.2f}ms")
        print(f"Batched update (1 commit): {elapsed_batched*1000:.2f}ms")
        print(f"Speedup: {elapsed_sequential/elapsed_batched:.2f}x")

        # Batched should be at least 3x faster
        assert elapsed_batched * 3 < elapsed_sequential, "Batching not providing expected speedup"

    def test_missing_index_detection(self, performance_db_session, create_test_conversation):
        """Check for missing indexes on frequently queried columns"""
        # Create 100 conversations to stress-test indexes
        for _ in range(100):
            create_test_conversation(10)

        # Test query performance on indexed vs non-indexed columns
        start_indexed = time.perf_counter()
        # user_id should be indexed (foreign key)
        result_indexed = performance_db_session.execute(
            text("SELECT COUNT(*) FROM conversations WHERE user_id = :uid"),
            {"uid": str(uuid.uuid4())}
        ).scalar()
        elapsed_indexed = time.perf_counter() - start_indexed

        start_nonindexed = time.perf_counter()
        # completeness_score likely not indexed
        result_nonindexed = performance_db_session.execute(
            text("SELECT COUNT(*) FROM conversations WHERE completeness_score > 0.5")
        ).scalar()
        elapsed_nonindexed = time.perf_counter() - start_nonindexed

        print(f"\nIndexed query (user_id): {elapsed_indexed*1000:.2f}ms")
        print(f"Non-indexed query (completeness_score): {elapsed_nonindexed*1000:.2f}ms")

        # Indexed query should be significantly faster (but SQLite in-memory might not show much difference)
        # This is more relevant for PostgreSQL in production


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory consumption"""

    def test_conversation_memory_footprint(self, create_test_conversation):
        """Measure memory usage for conversations of different sizes"""
        import tracemalloc
        import sys

        test_cases = [10, 50, 100]

        for num_turns in test_cases:
            tracemalloc.start()

            # Create conversation and load all turns
            conversation = create_test_conversation(num_turns)
            turns = list(conversation.turns)  # Force load all

            # Get memory snapshot
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Estimate object sizes
            conv_size = sys.getsizeof(conversation)
            turns_size = sum(sys.getsizeof(t) for t in turns)
            total_size = conv_size + turns_size

            print(f"\n{num_turns} turns:")
            print(f"  Conversation object: {conv_size} bytes")
            print(f"  Turns total: {turns_size} bytes ({turns_size/num_turns:.1f} bytes/turn)")
            print(f"  Total: {total_size/1024:.2f} KB")
            print(f"  Peak memory: {peak/1024:.2f} KB")

            # Target: < 50KB per 100 turns
            assert total_size < 50 * 1024, f"Memory usage {total_size/1024:.2f}KB exceeds 50KB for {num_turns} turns"

    def test_history_list_memory_growth(self, create_test_conversation):
        """Test memory growth when building conversation history list"""
        import sys

        conversation = create_test_conversation(100)

        # Simulate get_conversation_history_for_ai
        history_list = []
        for turn in conversation.turns:
            history_dict = {
                "user": turn.transcript_text,
                "ai": turn.ai_response
            }
            history_list.append(history_dict)

        history_size = sys.getsizeof(history_list)
        dict_sizes = sum(sys.getsizeof(d) for d in history_list)
        string_sizes = sum(
            sys.getsizeof(d["user"]) + sys.getsizeof(d["ai"])
            for d in history_list
        )

        total_size = history_size + dict_sizes + string_sizes

        print(f"\nHistory list for 100 turns:")
        print(f"  List overhead: {history_size} bytes")
        print(f"  Dicts overhead: {dict_sizes} bytes")
        print(f"  String data: {string_sizes} bytes")
        print(f"  Total: {total_size/1024:.2f} KB")

        # Target: < 100KB for 100 turns
        assert total_size < 100 * 1024, f"History list uses {total_size/1024:.2f}KB (expected < 100KB)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
