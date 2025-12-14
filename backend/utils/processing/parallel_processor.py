"""
Parallel Processing Utilities
Enables concurrent processing of charts and documents
"""

import logging
from typing import List, Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result from parallel processing task"""
    index: int
    success: bool
    result: Any
    error: Optional[str] = None
    duration_seconds: float = 0.0


class ParallelProcessor:
    """Process tasks in parallel with configurable workers"""
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize parallel processor
        
        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers
        self.stats = {
            "total_tasks": 0,
            "successful": 0,
            "failed": 0,
            "total_duration": 0.0
        }
    
    def process_batch(
        self,
        items: List[Any],
        process_func: Callable[[Any], Any],
        show_progress: bool = True
    ) -> List[ProcessingResult]:
        """
        Process items in parallel
        
        Args:
            items: List of items to process
            process_func: Function to apply to each item
            show_progress: Whether to log progress
        
        Returns:
            List of ProcessingResult objects
        """
        results = []
        self.stats["total_tasks"] += len(items)
        
        logger.info(f"Processing {len(items)} items with {self.max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(self._process_item, idx, item, process_func): idx
                for idx, item in enumerate(items)
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_index):
                result = future.result()
                results.append(result)
                completed += 1
                
                if result.success:
                    self.stats["successful"] += 1
                else:
                    self.stats["failed"] += 1
                
                self.stats["total_duration"] += result.duration_seconds
                
                if show_progress and completed % 10 == 0:
                    logger.info(f"Progress: {completed}/{len(items)} completed")
        
        # Sort by original index to maintain order
        results.sort(key=lambda x: x.index)
        
        logger.info(f"Batch complete: {self.stats['successful']} successful, {self.stats['failed']} failed")
        
        return results
    
    def _process_item(
        self,
        index: int,
        item: Any,
        process_func: Callable[[Any], Any]
    ) -> ProcessingResult:
        """Process a single item with error handling"""
        start_time = datetime.utcnow()
        
        try:
            result = process_func(item)
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                index=index,
                success=True,
                result=result,
                duration_seconds=duration
            )
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error processing item {index}: {str(e)}")
            
            return ProcessingResult(
                index=index,
                success=False,
                result=None,
                error=str(e),
                duration_seconds=duration
            )
    
    def get_stats(self) -> dict:
        """Get processing statistics"""
        avg_duration = (
            self.stats["total_duration"] / self.stats["total_tasks"]
            if self.stats["total_tasks"] > 0 else 0
        )
        
        success_rate = (
            self.stats["successful"] / self.stats["total_tasks"] * 100
            if self.stats["total_tasks"] > 0 else 0
        )
        
        return {
            "total_tasks": self.stats["total_tasks"],
            "successful": self.stats["successful"],
            "failed": self.stats["failed"],
            "success_rate": f"{success_rate:.1f}%",
            "avg_duration_seconds": f"{avg_duration:.2f}",
            "total_duration_seconds": f"{self.stats['total_duration']:.2f}"
        }


class ChartBatchProcessor:
    """Specialized processor for chart analysis"""
    
    def __init__(self, chart_analyzer, max_workers: int = 3):
        """
        Initialize chart batch processor
        
        Args:
            chart_analyzer: ChartAnalyzer instance
            max_workers: Maximum parallel workers (keep lower for API rate limits)
        """
        self.chart_analyzer = chart_analyzer
        self.processor = ParallelProcessor(max_workers=max_workers)
    
    def analyze_charts(
        self,
        chart_paths: List[str],
        analysis_type: str = "comprehensive"
    ) -> List[dict]:
        """
        Analyze multiple charts in parallel
        
        Args:
            chart_paths: List of paths to chart images
            analysis_type: Type of analysis to perform
        
        Returns:
            List of analysis results (empty dict for failures)
        """
        def analyze_single_chart(path: str) -> dict:
            """Wrapper for chart analysis"""
            try:
                if analysis_type == "comprehensive":
                    return self.chart_analyzer.analyze_chart_comprehensive(path)
                elif analysis_type == "data_extraction":
                    return self.chart_analyzer.extract_data_from_chart(path)
                else:
                    return self.chart_analyzer.analyze_chart(path)
            except Exception as e:
                logger.error(f"Chart analysis failed for {path}: {e}")
                return {}
        
        results = self.processor.process_batch(
            chart_paths,
            analyze_single_chart,
            show_progress=True
        )
        
        # Extract actual results (return empty dict for failures)
        return [r.result if r.success else {} for r in results]
    
    def get_stats(self) -> dict:
        """Get chart processing statistics"""
        return self.processor.get_stats()


class DocumentBatchProcessor:
    """Specialized processor for document extraction"""
    
    def __init__(self, extraction_pipeline, max_workers: int = 2):
        """
        Initialize document batch processor
        
        Args:
            extraction_pipeline: ExtractionPipeline instance
            max_workers: Maximum parallel workers
        """
        self.pipeline = extraction_pipeline
        self.processor = ParallelProcessor(max_workers=max_workers)
    
    def extract_documents(
        self,
        file_paths: List[str],
        output_dir: str
    ) -> List[dict]:
        """
        Extract multiple documents in parallel
        
        Args:
            file_paths: List of paths to documents
            output_dir: Output directory for results
        
        Returns:
            List of extraction results
        """
        def extract_single_doc(path: str) -> dict:
            """Wrapper for document extraction"""
            try:
                return self.pipeline.process_document(path, output_dir)
            except Exception as e:
                logger.error(f"Document extraction failed for {path}: {e}")
                return {"error": str(e), "file_path": path}
        
        results = self.processor.process_batch(
            file_paths,
            extract_single_doc,
            show_progress=True
        )
        
        return [r.result for r in results]
    
    def get_stats(self) -> dict:
        """Get document processing statistics"""
        return self.processor.get_stats()


if __name__ == "__main__":
    # Test parallel processor
    import time
    
    def slow_function(x):
        """Simulate slow processing"""
        time.sleep(0.1)
        return x * 2
    
    processor = ParallelProcessor(max_workers=4)
    items = list(range(20))
    
    results = processor.process_batch(items, slow_function)
    
    print(f"Processed {len(results)} items")
    print(f"Stats: {processor.get_stats()}")
    print(f"First 5 results: {[r.result for r in results[:5]]}")
