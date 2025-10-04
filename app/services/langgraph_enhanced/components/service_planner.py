"""
서비스 계획자
단일 책임: 필요한 서비스들을 어떻게 실행할지 계획하는 역할만 담당
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from ..config import get_enhanced_settings
from ..error_handler import safe_execute_enhanced


class ExecutionStrategy(Enum):
    """실행 전략"""
    SEQUENTIAL = "sequential"  # 순차 실행
    PARALLEL = "parallel"      # 병렬 실행
    HYBRID = "hybrid"         # 혼합 실행


@dataclass
class ServicePlan:
    """서비스 실행 계획"""
    strategy: ExecutionStrategy
    service_groups: List[List[str]]  # 병렬 실행할 서비스 그룹들
    estimated_time: float
    priority_order: List[str]
    dependencies: Dict[str, List[str]]


class ServicePlanner:
    """서비스 계획자"""
    
    def __init__(self):
        self.settings = get_enhanced_settings()
        self.service_dependencies = self._load_service_dependencies()
        self.service_priorities = self._load_service_priorities()
    
    def _load_service_dependencies(self) -> Dict[str, List[str]]:
        """서비스 의존성 로드"""
        return {
            "visualization": ["financial_data"],  # 시각화는 금융 데이터가 필요
            "analysis": ["financial_data"],       # 분석은 금융 데이터가 필요
            "news": [],                          # 뉴스는 독립적
            "knowledge": [],                     # 지식은 독립적
            "financial_data": []                 # 금융 데이터는 독립적
        }
    
    def _load_service_priorities(self) -> Dict[str, int]:
        """서비스 우선순위 로드 (낮을수록 높은 우선순위)"""
        return {
            "financial_data": 1,
            "knowledge": 2,
            "news": 3,
            "analysis": 4,
            "visualization": 5
        }
    
    def create_service_plan(self, 
                          required_services: List[str], 
                          complexity_level: str,
                          user_context: Dict[str, Any]) -> ServicePlan:
        """서비스 실행 계획 생성"""
        try:
            # 서비스 의존성 고려하여 실행 순서 결정
            ordered_services = self._order_services_by_dependency(required_services)
            
            # 실행 전략 결정
            strategy = self._determine_execution_strategy(ordered_services, complexity_level)
            
            # 서비스 그룹 생성
            service_groups = self._create_service_groups(ordered_services, strategy)
            
            # 예상 시간 계산
            estimated_time = self._estimate_execution_time(service_groups, strategy)
            
            # 우선순위 순서 결정
            priority_order = self._determine_priority_order(ordered_services)
            
            # 의존성 맵 생성
            dependencies = self._build_dependency_map(ordered_services)
            
            return ServicePlan(
                strategy=strategy,
                service_groups=service_groups,
                estimated_time=estimated_time,
                priority_order=priority_order,
                dependencies=dependencies
            )
            
        except Exception as e:
            # 에러 발생 시 기본 계획 반환
            return self._create_fallback_plan(required_services)
    
    def _order_services_by_dependency(self, services: List[str]) -> List[str]:
        """의존성을 고려하여 서비스 순서 결정"""
        ordered = []
        remaining = set(services)
        
        while remaining:
            # 의존성이 모두 해결된 서비스 찾기
            ready_services = []
            for service in remaining:
                dependencies = self.service_dependencies.get(service, [])
                if all(dep in ordered for dep in dependencies):
                    ready_services.append(service)
            
            if not ready_services:
                # 순환 의존성 방지: 남은 서비스 중 우선순위가 높은 것부터
                ready_services = [min(remaining, key=lambda s: self.service_priorities.get(s, 999))]
            
            # 우선순위 순으로 정렬
            ready_services.sort(key=lambda s: self.service_priorities.get(s, 999))
            ordered.extend(ready_services)
            remaining -= set(ready_services)
        
        return ordered
    
    def _determine_execution_strategy(self, 
                                    services: List[str], 
                                    complexity_level: str) -> ExecutionStrategy:
        """실행 전략 결정"""
        
        # 복잡한 질문이고 여러 서비스가 필요한 경우 병렬 실행
        if (complexity_level in ["complex", "multi_faceted"] and 
            len(services) >= self.settings.service_count_threshold):
            return ExecutionStrategy.PARALLEL
        
        # 서비스가 적고 의존성이 있는 경우 순차 실행
        if len(services) <= 2:
            return ExecutionStrategy.SEQUENTIAL
        
        # 그 외의 경우 혼합 실행
        return ExecutionStrategy.HYBRID
    
    def _create_service_groups(self, 
                             services: List[str], 
                             strategy: ExecutionStrategy) -> List[List[str]]:
        """서비스 그룹 생성"""
        
        if strategy == ExecutionStrategy.SEQUENTIAL:
            # 순차 실행: 각 서비스를 개별 그룹으로
            return [[service] for service in services]
        
        elif strategy == ExecutionStrategy.PARALLEL:
            # 병렬 실행: 의존성이 없는 서비스들을 그룹화
            return self._group_parallel_services(services)
        
        else:  # HYBRID
            # 혼합 실행: 의존성과 우선순위를 고려하여 그룹화
            return self._group_hybrid_services(services)
    
    def _group_parallel_services(self, services: List[str]) -> List[List[str]]:
        """병렬 실행 가능한 서비스 그룹화"""
        groups = []
        remaining = services.copy()
        
        while remaining:
            # 현재 그룹에 추가할 수 있는 서비스들 찾기
            current_group = []
            dependencies_resolved = set()
            
            for service in remaining:
                dependencies = self.service_dependencies.get(service, [])
                if all(dep in dependencies_resolved for dep in dependencies):
                    current_group.append(service)
                    dependencies_resolved.add(service)
            
            if not current_group:
                # 의존성 문제가 있는 경우 첫 번째 서비스만 그룹에 추가
                current_group = [remaining[0]]
            
            groups.append(current_group)
            remaining = [s for s in remaining if s not in current_group]
        
        return groups
    
    def _group_hybrid_services(self, services: List[str]) -> List[List[str]]:
        """혼합 실행을 위한 서비스 그룹화"""
        groups = []
        remaining = services.copy()
        
        while remaining:
            # 첫 번째 그룹: 의존성이 없는 서비스들 (병렬 실행 가능)
            first_group = []
            for service in remaining:
                dependencies = self.service_dependencies.get(service, [])
                if not dependencies:
                    first_group.append(service)
            
            if first_group:
                # 병렬 실행 가능한 서비스들을 하나의 그룹으로
                groups.append(first_group)
                remaining = [s for s in remaining if s not in first_group]
            else:
                # 의존성이 있는 경우 첫 번째 서비스만 그룹에 추가
                groups.append([remaining[0]])
                remaining = remaining[1:]
        
        return groups
    
    def _estimate_execution_time(self, 
                               service_groups: List[List[str]], 
                               strategy: ExecutionStrategy) -> float:
        """실행 시간 추정"""
        base_time_per_service = 2.0  # 기본 서비스당 2초
        
        if strategy == ExecutionStrategy.SEQUENTIAL:
            # 순차 실행: 모든 서비스 시간 합계
            total_services = sum(len(group) for group in service_groups)
            return total_services * base_time_per_service
        
        elif strategy == ExecutionStrategy.PARALLEL:
            # 병렬 실행: 가장 긴 그룹의 시간
            max_group_time = max(len(group) for group in service_groups) * base_time_per_service
            return max_group_time
        
        else:  # HYBRID
            # 혼합 실행: 그룹별로 순차 실행, 그룹 내에서는 병렬 실행
            total_time = 0
            for group in service_groups:
                group_time = len(group) * base_time_per_service * 0.7  # 병렬 효과 고려
                total_time += group_time
            return total_time
    
    def _determine_priority_order(self, services: List[str]) -> List[str]:
        """우선순위 순서 결정"""
        return sorted(services, key=lambda s: self.service_priorities.get(s, 999))
    
    def _build_dependency_map(self, services: List[str]) -> Dict[str, List[str]]:
        """의존성 맵 생성"""
        return {
            service: self.service_dependencies.get(service, [])
            for service in services
        }
    
    def _create_fallback_plan(self, services: List[str]) -> ServicePlan:
        """폴백 계획 생성"""
        return ServicePlan(
            strategy=ExecutionStrategy.SEQUENTIAL,
            service_groups=[[service] for service in services[:2]],  # 최대 2개 서비스만
            estimated_time=4.0,
            priority_order=services[:2],
            dependencies={}
        )
