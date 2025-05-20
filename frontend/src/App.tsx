import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Table, Layout, Typography, Input, Space, Spin, Button, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { FilterValue, TablePaginationConfig } from 'antd/es/table/interface';
import { ProgramData } from './types';
import ProgramDetail from './ProgramDetail';
import SearchBar from './components/SearchBar';

const { Header, Content } = Layout;
const { Title } = Typography;
const { Search } = Input;

// 定义筛选条件类型
interface FilterState {
  discipline: string[];
  sub_discipline: string[];
  university: string[];
  academic_level: string[];
  programme_type: string[];
  fee_range: string[];
}

// 筛选器选项接口
interface FilterOptions {
  disciplines: { text: string; value: string }[];
  subDisciplines: { text: string; value: string }[];
  universities: { text: string; value: string }[];
  academicLevels: { text: string; value: string }[];
  programmeTypes: { text: string; value: string }[];
  feeRanges: { text: string; value: string }[];
}

// 排序状态接口
interface SortState {
  field: string | null;
  order: 'ascend' | 'descend' | null;
}

// 定义常量
const FEE_RANGES = [
  { text: '10万以下', value: '0-100000' },
  { text: '10-15万', value: '100000-150000' },
  { text: '15-20万', value: '150000-200000' },
  { text: '20万以上', value: '200000-999999999' }
];

const FEE_LABELS: Record<string, string> = {
  '0-100000': '10万以下',
  '100000-150000': '10-15万',
  '150000-200000': '15-20万',
  '200000-999999999': '20万以上'
};

// 初始筛选状态
const INITIAL_FILTER_STATE: FilterState = {
  discipline: [],
  sub_discipline: [],
  university: [],
  academic_level: [],
  programme_type: [],
  fee_range: []
};

// 筛选服务类
class FilterService {
  // 应用所有筛选条件到数据集
  static applyFilters(
    data: ProgramData[], 
    searchText: string, 
    filterState: FilterState
  ): ProgramData[] {
    console.log("===== FilterService.applyFilters =====");
    console.log(`输入数据集: ${data.length}条记录`);
    console.log(`搜索文本: "${searchText}"`);
    console.log("筛选条件:", JSON.stringify(filterState, null, 2));
    
    if (!data || !data.length) return [];
    
    // 从原始数据创建一个副本
    let result = [...data];
    
    // 应用文本搜索
    if (searchText) {
      result = result.filter(program => 
        program.program_name.toLowerCase().includes(searchText.toLowerCase()) || 
        program.university.toLowerCase().includes(searchText.toLowerCase()) ||
        program.discipline.toLowerCase().includes(searchText.toLowerCase())
      );
      console.log(`文本搜索后: ${result.length}条记录`);
    }
    
    // 应用筛选条件 - 确保所有字段都被严格比较
    if (filterState.discipline.length > 0) {
      result = result.filter(program => 
        program.discipline && filterState.discipline.includes(program.discipline));
      console.log(`学科筛选后: ${result.length}条记录`);
    }
    
    if (filterState.sub_discipline.length > 0) {
      result = result.filter(program => 
        program.sub_discipline && filterState.sub_discipline.includes(program.sub_discipline));
      console.log(`子学科筛选后: ${result.length}条记录`);
    }
    
    if (filterState.university.length > 0) {
      result = result.filter(program => 
        program.university && filterState.university.includes(program.university));
      console.log(`大学筛选后: ${result.length}条记录`);
    }
    
    if (filterState.academic_level.length > 0) {
      result = result.filter(program => 
        program.academic_level && filterState.academic_level.includes(program.academic_level));
      console.log(`学术等级筛选后: ${result.length}条记录`);
    }
    
    if (filterState.programme_type.length > 0) {
      result = result.filter(program => 
        program.programme_type && filterState.programme_type.includes(program.programme_type));
      console.log(`项目类型筛选后: ${result.length}条记录`);
    }
    
    if (filterState.fee_range.length > 0) {
      result = result.filter(program => {
        if (!program.international_total_fee) return false;
        
        return filterState.fee_range.some(range => {
          const [min, max] = range.split('-').map(Number);
          return program.international_total_fee.fee_lower >= min && 
                 program.international_total_fee.fee_lower < max;
        });
      });
      console.log(`费用范围筛选后: ${result.length}条记录`);
    }
    
    console.log(`最终结果: ${result.length}条记录`);
    console.log("=====================================");
    return result;
  }
  
  // 应用排序到数据集
  static applySorter(
    data: ProgramData[],
    sortField: string | null,
    sortOrder: 'ascend' | 'descend' | null
  ): ProgramData[] {
    if (!sortField || !sortOrder) {
      return data;
    }
    
    return [...data].sort((a, b) => {
      let aValue: any;
      let bValue: any;
      
      // 处理嵌套字段的特殊情况
      if (sortField === 'international_fee') {
        aValue = a.international_total_fee.fee_lower;
        bValue = b.international_total_fee.fee_lower;
      } else {
        aValue = a[sortField as keyof ProgramData];
        bValue = b[sortField as keyof ProgramData];
      }
      
      // 字符串类型进行本地化比较
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortOrder === 'ascend' 
          ? aValue.localeCompare(bValue, 'zh-CN')
          : bValue.localeCompare(aValue, 'zh-CN');
      }
      
      // 数字类型直接比较
      return sortOrder === 'ascend' ? (aValue - bValue) : (bValue - aValue);
    });
  }

  // 计算排除特定筛选条件后的数据集
  static calculateFilteredDataExcluding(
    data: ProgramData[],
    searchText: string,
    filterState: FilterState,
    excludeFilterKey: keyof FilterState
  ): ProgramData[] {
    // 创建筛选条件的副本，并移除要排除的条件
    const tempFilterState = { ...filterState };
    tempFilterState[excludeFilterKey] = [];
    
    // 应用剩余的筛选条件
    return this.applyFilters(data, searchText, tempFilterState);
  }

  // 获取并排序唯一值
  static getUniqueValuesSorted(data: ProgramData[], field: keyof ProgramData): string[] {
    return [...new Set(data.map(item => item[field] as string))]
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b, 'zh-CN'));
  }

  // 获取原始数据中所有可用的唯一值（不受筛选影响）
  static getAllAvailableOptions(originalData: ProgramData[]): FilterOptions {
    console.log("===== FilterService.getAllAvailableOptions =====");
    console.log(`原始数据集: ${originalData.length}条记录`);
    
    const options = {
      disciplines: this.getUniqueValuesSorted(originalData, 'discipline')
        .map(v => ({ text: v, value: v })),
      subDisciplines: this.getUniqueValuesSorted(originalData, 'sub_discipline')
        .map(v => ({ text: v, value: v })),
      universities: this.getUniqueValuesSorted(originalData, 'university')
        .map(v => ({ text: v, value: v })),
      academicLevels: this.getUniqueValuesSorted(originalData, 'academic_level')
        .map(v => ({ text: v, value: v })),
      programmeTypes: this.getUniqueValuesSorted(originalData, 'programme_type')
        .map(v => ({ text: v, value: v })),
      feeRanges: FEE_RANGES // 使用预定义的费用范围
    };
    
    console.log(`生成的筛选选项: 学科(${options.disciplines.length}), 子学科(${options.subDisciplines.length}), 大学(${options.universities.length}), 学术等级(${options.academicLevels.length}), 项目类型(${options.programmeTypes.length}), 费用范围(${options.feeRanges.length})`);
    console.log("==============================================");
    
    return options;
  }

  // 生成筛选选项
  static generateFilterOptions(
    data: ProgramData[],
    searchText: string,
    filterState: FilterState,
    showAllOptions: boolean = false,
    originalData: ProgramData[] = []
  ): FilterOptions {
    console.log("===== FilterService.generateFilterOptions =====");
    console.log(`数据集: ${data.length}条记录`);
    console.log(`showAllOptions: ${showAllOptions}`);
    console.log(`原始数据集大小: ${originalData.length}条记录`);
    console.log("当前筛选条件:", JSON.stringify(filterState, null, 2));
    
    // 始终使用全部选项模式，确保无论筛选状态如何，都显示所有可用的筛选选项
    // 这样即使当前筛选结果为空，用户也能看到并选择所有可能的筛选值
    console.log("使用全部选项模式");
    
    // 使用原始数据集生成所有可能的选项
    if (originalData.length > 0) {
      return this.getAllAvailableOptions(originalData);
    } else {
      return this.getAllAvailableOptions(data);
    }
  }

  // 从Ant Design表格的filters对象构建FilterState
  static buildFilterStateFromTable(tableFilters: Record<string, FilterValue | null>): FilterState {
    console.log("===== FilterService.buildFilterStateFromTable =====");
    console.log("表格筛选条件:", tableFilters);
    
    const result = {
      discipline: Array.isArray(tableFilters.discipline) ? tableFilters.discipline.map(String) : [],
      sub_discipline: Array.isArray(tableFilters.sub_discipline) ? tableFilters.sub_discipline.map(String) : [],
      university: Array.isArray(tableFilters.university) ? tableFilters.university.map(String) : [],
      academic_level: Array.isArray(tableFilters.academic_level) ? tableFilters.academic_level.map(String) : [],
      programme_type: Array.isArray(tableFilters.programme_type) ? tableFilters.programme_type.map(String) : [],
      fee_range: Array.isArray(tableFilters.fee_range) ? tableFilters.fee_range.map(String) : []
    };
    
    console.log("构建的FilterState:", result);
    console.log("==============================================");
    
    return result;
  }
}

// 筛选标签组件
interface FilterTagsProps {
  filteredInfo: FilterState;
  onRemoveFilter: (key: keyof FilterState, value: string) => void;
  onClearAllFilters: () => void;
}

const FilterTags: React.FC<FilterTagsProps> = ({ 
  filteredInfo, 
  onRemoveFilter, 
  onClearAllFilters 
}) => {
  const activeFilters: React.ReactNode[] = [];
  
  // 生成学科筛选标签
  if (filteredInfo.discipline.length > 0) {
    filteredInfo.discipline.forEach(value => {
      activeFilters.push(
        <Tag closable key={`discipline-${value}`} onClose={() => onRemoveFilter('discipline', value)}>
          学科: {value}
        </Tag>
      );
    });
  }
  
  // 生成子学科筛选标签
  if (filteredInfo.sub_discipline.length > 0) {
    filteredInfo.sub_discipline.forEach(value => {
      activeFilters.push(
        <Tag closable key={`sub_discipline-${value}`} onClose={() => onRemoveFilter('sub_discipline', value)}>
          子学科: {value}
        </Tag>
      );
    });
  }
  
  // 生成大学筛选标签
  if (filteredInfo.university.length > 0) {
    filteredInfo.university.forEach(value => {
      activeFilters.push(
        <Tag closable key={`university-${value}`} onClose={() => onRemoveFilter('university', value)}>
          发证学校: {value}
        </Tag>
      );
    });
  }
  
  // 生成学业阶段筛选标签
  if (filteredInfo.academic_level.length > 0) {
    filteredInfo.academic_level.forEach(value => {
      activeFilters.push(
        <Tag closable key={`academic_level-${value}`} onClose={() => onRemoveFilter('academic_level', value)}>
          学业阶段: {value}
        </Tag>
      );
    });
  }
  
  // 生成项目类型筛选标签
  if (filteredInfo.programme_type.length > 0) {
    filteredInfo.programme_type.forEach(value => {
      activeFilters.push(
        <Tag closable key={`programme_type-${value}`} onClose={() => onRemoveFilter('programme_type', value)}>
          项目类型: {value}
        </Tag>
      );
    });
  }
  
  // 生成费用范围筛选标签
  if (filteredInfo.fee_range.length > 0) {
    filteredInfo.fee_range.forEach(value => {
      activeFilters.push(
        <Tag closable key={`fee_range-${value}`} onClose={() => onRemoveFilter('fee_range', value)}>
          费用: {FEE_LABELS[value] || value}
        </Tag>
      );
    });
  }
  
  if (activeFilters.length === 0) {
    return null;
  }
  
  return (
    <div style={{ marginBottom: 16 }}>
      <Space size={[0, 8]} wrap>
        <span>已筛选: </span>
        {activeFilters}
        <Button type="link" onClick={onClearAllFilters}>清除全部</Button>
      </Space>
    </div>
  );
};

// 生成表格列
const generateColumns = (
  filterOptions: FilterOptions, 
  filteredInfo: FilterState, 
  handleViewDetails: (program: ProgramData) => void
): ColumnsType<ProgramData> => [
    {
      title: '学科',
      dataIndex: 'discipline',
      key: 'discipline',
      sorter: (a, b) => a.discipline.localeCompare(b.discipline),
      filters: filterOptions.disciplines,
      filteredValue: filteredInfo.discipline,
      filterSearch: true,
      filterMode: 'tree',
      onFilter: () => true,
    },
    {
      title: '子学科',
      dataIndex: 'sub_discipline',
      key: 'sub_discipline',
      sorter: (a, b) => a.sub_discipline.localeCompare(b.sub_discipline),
      filters: filterOptions.subDisciplines,
      filteredValue: filteredInfo.sub_discipline,
      filterSearch: true,
      filterMode: 'tree',
      onFilter: () => true,
    },
    {
      title: '项目名称',
      dataIndex: 'program_name',
      key: 'program_name',
      sorter: (a, b) => a.program_name.localeCompare(b.program_name),
    },
    {
      title: '发证学校',
      dataIndex: 'university',
      key: 'university',
      sorter: (a, b) => a.university.localeCompare(b.university),
      filters: filterOptions.universities,
      filteredValue: filteredInfo.university,
      filterSearch: true,
      filterMode: 'tree',
      onFilter: () => true,
    },
    {
      title: '学业阶段',
      dataIndex: 'academic_level',
      key: 'academic_level',
      filters: filterOptions.academicLevels,
      filteredValue: filteredInfo.academic_level,
      filterSearch: true,
      filterMode: 'tree',
      onFilter: () => true,
    },
    {
      title: '项目类型',
      dataIndex: 'programme_type',
      key: 'programme_type',
      filters: filterOptions.programmeTypes,
      filteredValue: filteredInfo.programme_type,
      filterSearch: true,
      filterMode: 'tree',
      onFilter: () => true,
    },
    {
      title: '线上托福',
      key: 'toefl_score',
      render: (_, record) => {
        if (!record.admission_requirements || 
            !record.admission_requirements.international) {
          return '-';
        }
        
        // 查找国际生英语要求
        const englishReq = record.admission_requirements.international.find(
          req => req.requirement_type === 'english_language'
        );
        
        if (!englishReq || !englishReq.specific_requirements) {
          return '-';
        }
        
        // 查找所有TOEFL要求
        const toeflReqs = englishReq.specific_requirements.filter(
          req => req.requirement_type === 'TOEFL'
        );
        
        if (!toeflReqs || toeflReqs.length === 0) {
          return '-';
        }
        
        // 查找线上托福分数
        const onlineToefl = toeflReqs.find(toefl => {
          const score = Number(toefl.grade);
          const description = toefl.requirement_description?.toLowerCase() || '';
          
          // 检查是否为线上托福分数
          return (!isNaN(score) && score <= 120) || 
                 description.includes('internet-based') ||
                 description.includes('ibt');
        });
        
        if (onlineToefl) {
          // 如果描述中包含分数，优先使用描述中的分数
          const descMatch = onlineToefl.requirement_description?.match(/\d+/);
          if (descMatch) {
            return descMatch[0];
          }
          return onlineToefl.grade;
        }
        
        return '-';
      }
    },
    {
      title: '雅思',
      key: 'ielts_score',
      render: (_, record) => {
        if (!record.admission_requirements || 
            !record.admission_requirements.international) {
          return '-';
        }
        
        // 查找国际生英语要求
        const englishReq = record.admission_requirements.international.find(
          req => req.requirement_type === 'english_language'
        );
        
        if (!englishReq || !englishReq.specific_requirements) {
          return '-';
        }
        
        // 查找IELTS要求
        const ieltsReq = englishReq.specific_requirements.find(
          req => req.requirement_type === 'IELTS'
        );
        
        if (!ieltsReq) {
          return '-';
        }
        
        return `${ieltsReq.grade}`;
      }
    },
    {
      title: '国际生费用',
      key: 'international_fee',
      render: (_, record) => (
        <span>
          S${record.international_total_fee.fee_lower.toLocaleString()} - S${record.international_total_fee.fee_upper.toLocaleString()}
        </span>
      ),
      sorter: (a, b) => a.international_total_fee.fee_lower - b.international_total_fee.fee_lower,
      filters: filterOptions.feeRanges,
      filteredValue: filteredInfo.fee_range,
      filterSearch: true,
      filterMode: 'tree',
      onFilter: () => true,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button type="primary" onClick={() => handleViewDetails(record)}>查看详情</Button>
          <a href={record.program_link} target="_blank" rel="noopener noreferrer">官方网站</a>
        </Space>
      ),
    },
  ];

const App: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [data, setData] = useState<ProgramData[]>([]);
  const [filteredData, setFilteredData] = useState<ProgramData[]>([]);
  const [searchText, setSearchText] = useState<string>('');
  const [selectedProgram, setSelectedProgram] = useState<ProgramData | null>(null);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  
  // 向量搜索相关状态
  const [isVectorSearch, setIsVectorSearch] = useState<boolean>(false);
  const [isLLMSearch, setIsLLMSearch] = useState<boolean>(false);
  const [searchLoading, setSearchLoading] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchWeights, setSearchWeights] = useState<Record<string, number> | null>(null);
  const [aiThinkingProcess, setAiThinkingProcess] = useState<string>('');
  const [isAIStreaming, setIsAIStreaming] = useState<boolean>(false);
  
  // 跟踪当前应用的筛选条件
  const [filteredInfo, setFilteredInfo] = useState<FilterState>(INITIAL_FILTER_STATE);
  
  // 跟踪排序状态
  const [sortInfo, setSortInfo] = useState<SortState>({
    field: null,
    order: null
  });
  
  // 用于跟踪前一次的筛选条件和搜索文本
  const prevFilteredInfoRef = useRef<string>('');
  const prevSearchTextRef = useRef<string>('');

  // 当前表格的分页设置
  const [pagination, setPagination] = useState<TablePaginationConfig>({
    current: 1,
    pageSize: 10,
  });

  // 加载数据
  useEffect(() => {
    fetch('/SIM_programs.json')
      .then(response => response.json())
      .then(data => {
        setData(data);
        setFilteredData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching data:', error);
        setLoading(false);
      });
  }, []);

  // 处理筛选条件变化，仅当变化时重置页码
  useEffect(() => {
    // 将当前筛选条件序列化为字符串，便于比较
    const currentFilteredInfoStr = JSON.stringify(filteredInfo);
    
    // 检查筛选条件或搜索文本是否变化
    const filtersChanged = currentFilteredInfoStr !== prevFilteredInfoRef.current;
    const searchChanged = searchText !== prevSearchTextRef.current;
    
    // 如果有变化，重置分页到第一页
    if ((filtersChanged || searchChanged) && pagination.current !== 1) {
      setPagination(prev => ({
        ...prev,
        current: 1
      }));
    }
    
    // 更新前一次的筛选条件和搜索文本引用
    prevFilteredInfoRef.current = currentFilteredInfoStr;
    prevSearchTextRef.current = searchText;
  }, [filteredInfo, searchText, pagination.current]);
  
  // 处理数据过滤和排序
  useEffect(() => {
    console.log("===== 数据筛选 useEffect 触发 =====");
    console.log("触发原因: searchText, filteredInfo, sortInfo, isLLMSearch 或 isAIStreaming 变化");
    console.log(`isAIStreaming: ${isAIStreaming}`);
    console.log(`isLLMSearch: ${isLLMSearch}`);
    console.log(`筛选条件:`, JSON.stringify(filteredInfo, null, 2));
    console.log(`搜索文本: "${searchText}"`);
    
    // 流式处理进行中时不应用筛选（因为数据还在生成中）
    if (!isAIStreaming) {
      console.log("应用筛选逻辑");

      // 如果是LLM搜索模式，并且AI返回了具体的筛选条件 (filteredInfo 不是初始状态),
      // 则不使用searchText进行关键词过滤，因为AI的筛选条件已经包含了用户的意图。
      // 否则，使用searchText进行关键词过滤 (适用于普通搜索，或LLM未返回有效筛选条件的情况)。
      const keywordFilterText = (isLLMSearch && JSON.stringify(filteredInfo) !== JSON.stringify(INITIAL_FILTER_STATE))
                               ? '' 
                               : searchText;
      
      if (isLLMSearch && JSON.stringify(filteredInfo) !== JSON.stringify(INITIAL_FILTER_STATE)) {
        console.log("LLM搜索模式且有AI筛选条件，关键词搜索将使用空字符串。");
      } else {
        console.log(`将使用关键词: "${keywordFilterText}" 进行过滤。`);
      }

      // 使用筛选服务应用所有筛选条件
      let result = FilterService.applyFilters(data, keywordFilterText, filteredInfo);
      
      // 应用排序
      if (sortInfo.field && sortInfo.order) {
        console.log(`应用排序: ${sortInfo.field} ${sortInfo.order}`);
        result = FilterService.applySorter(result, sortInfo.field, sortInfo.order);
      }
      
      // 更新筛选后的数据
      console.log(`筛选后数据数量: ${result.length}`);
      setFilteredData(result);
    } else {
      console.log("流式处理进行中，跳过筛选逻辑");
    }
    console.log("====================================");
  }, [data, searchText, filteredInfo, sortInfo, isAIStreaming, isLLMSearch]);

  // 生成动态筛选器选项，基于当前筛选结果
  const filterOptions = useMemo(() => {
    console.log("===== filterOptions useMemo 触发 =====");
    console.log(`当前筛选结果数量: ${filteredData.length}`);
    
    // 始终显示所有可用选项，无论是否有筛选结果
    // 这确保了无论是AI筛选还是手动筛选，筛选菜单中始终显示所有可用选项
    const showAllOptions = true;
    console.log(`是否显示全部选项: ${showAllOptions}`);
    
    const options = FilterService.generateFilterOptions(
      data, 
      searchText, 
      filteredInfo,
      showAllOptions, 
      data // 传入原始数据，用于生成所有可用选项
    );
    
    console.log("生成的筛选选项数量:");
    console.log(`- 学科: ${options.disciplines.length}`);
    console.log(`- 子学科: ${options.subDisciplines.length}`);
    console.log(`- 大学: ${options.universities.length}`);
    console.log(`- 学术等级: ${options.academicLevels.length}`);
    console.log(`- 项目类型: ${options.programmeTypes.length}`);
    console.log(`- 费用范围: ${options.feeRanges.length}`);
    console.log("====================================");
    
    return options;
  }, [data, searchText, filteredInfo]);
  
  // 处理搜索
  const handleSearch = async (value: string, useVectorSearch: boolean = false, useLLMSearch: boolean = false) => {
    if (!value.trim()) {
      // 如果搜索内容为空，则不执行任何搜索，清空状态
      setSearchText('');
      setIsVectorSearch(false);
      setIsLLMSearch(false);
      setSearchWeights(null);
      setAiThinkingProcess('');
      setSearchError(null);
      // 重置为初始数据
      if (data.length > 0) {
        setFilteredData(data);
      }
      return;
    }

    setSearchText(value);
    setIsVectorSearch(useVectorSearch);
    setIsLLMSearch(useLLMSearch);
    setSearchWeights(null);
    setAiThinkingProcess('');
    setSearchError(null);

    // 如果是AI流式智能搜索
    if (useLLMSearch && value) {
      // 在开始AI搜索前清除所有已应用的筛选条件
      console.log("===== AI搜索开始 - 自动清除所有已应用的筛选条件 =====");
      setFilteredInfo(INITIAL_FILTER_STATE);
      
      setIsAIStreaming(true);
      setSearchLoading(true);
      setFilteredData([]);

      const eventSource = new EventSource(`http://localhost:5000/api/ai_stream_search?query=${encodeURIComponent(value)}`);
      let thinkingProcessBuffer = '';
      let receivedJsonInstruction = false;
      let currentJsonBuffer = '';
      let endOfThoughtsReceived = false;

      eventSource.onmessage = (event) => {
        const streamData = event.data;
        console.log(">>> FRONTEND SSE Raw Data:", streamData);

        if (streamData === "<<STREAM_END>>") {
          console.log(">>> FRONTEND Received <<STREAM_END>>. Final JSON buffer:", currentJsonBuffer, "End of thoughts received:", endOfThoughtsReceived, "JSON instruction received:", receivedJsonInstruction);
          if (endOfThoughtsReceived && currentJsonBuffer.trim()) {
            try {
              const parsedInstruction = JSON.parse(currentJsonBuffer.trim());
              console.log(">>> FRONTEND Parsed Instruction from final buffer:", parsedInstruction);
              if (parsedInstruction && parsedInstruction.filters) {
                const aiFilters: Partial<FilterState> = {};
                for (const key in parsedInstruction.filters) {
                  if (Object.prototype.hasOwnProperty.call(INITIAL_FILTER_STATE, key)) {
                    aiFilters[key as keyof FilterState] = parsedInstruction.filters[key];
                  }
                }
                
                // 提取应用的筛选字段名称，用于日志和状态
                const appliedFields = Object.keys(aiFilters);
                if (appliedFields.length > 0) {
                  console.log(`>>> FRONTEND AI suggested filters for fields: ${appliedFields.join(', ')}`);
                } else {
                  console.log(">>> FRONTEND AI didn't suggest any specific filters");
                }
                
                // 合并，确保所有字段都存在，即使AI没有提供
                const newFilterState = { ...INITIAL_FILTER_STATE, ...aiFilters }; 
                
                // 应用AI筛选结果到表格筛选状态
                setFilteredInfo(newFilterState);
                
                receivedJsonInstruction = true;
                console.log(">>> FRONTEND Successfully applied AI filters from final buffer.");
              } else {
                setSearchError("AI返回的最终筛选指令格式错误。");
              }
            } catch (e) {
              console.error(">>> FRONTEND Failed to parse AI filter instruction JSON from final buffer:", e, "Raw string was:", currentJsonBuffer.trim());
              if (!receivedJsonInstruction) setSearchError("解析AI最终筛选指令失败。");
            }
          }
          setIsAIStreaming(false);
          setSearchLoading(false);
          eventSource.close();
          if (!receivedJsonInstruction) {
            setSearchError("AI未能提供有效的筛选指令或指令解析失败。");
          }
          return;
        }

        if (streamData === "<END_OF_THOUGHTS>") {
          console.log(">>> FRONTEND Received <END_OF_THOUGHTS> marker.");
          endOfThoughtsReceived = true;
          return;
        }

        if (endOfThoughtsReceived) {
          currentJsonBuffer += streamData;
          console.log(">>> FRONTEND Accumulating JSON part:", streamData, "Current JSON buffer:", currentJsonBuffer);
        } else {
          setAiThinkingProcess(prev => prev + streamData);
          console.log(">>> FRONTEND Appending to thinking process:", streamData);
        }
      };

      eventSource.onerror = (err) => {
        console.error("EventSource failed:", err);
        setSearchError("与AI服务连接失败。");
        setIsAIStreaming(false);
        setSearchLoading(false);
        eventSource.close();
      };

    } else if (useVectorSearch && value) { // 原有的向量搜索逻辑 (非流式)
      try {
        setSearchLoading(true);
        setSearchError(null);
        
        // 调用API
        const apiUrl = `http://localhost:5000/api/search?query=${encodeURIComponent(value)}&use_vector=${useVectorSearch}&use_llm=${useLLMSearch}`;
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
          throw new Error(`API错误: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
          throw new Error(data.error);
        }
        
        // 更新搜索结果 - 在向量搜索模式下，API直接返回筛选后的结果集
        const vectorResults = data.results;
        
        // 保存权重信息（仅用于LLM搜索）
        if (useLLMSearch && data.weights) {
          setSearchWeights(data.weights);
        }
        
        // 在有筛选条件的情况下，对API返回的结果进一步应用筛选
        if (Object.values(filteredInfo).some(arr => arr.length > 0)) {
          const filteredVectorResults = FilterService.applyFilters(vectorResults, '', filteredInfo);
          setFilteredData(filteredVectorResults);
        } else {
          // 没有筛选条件，直接使用API结果
          setFilteredData(vectorResults);
        }
        
      } catch (error) {
        console.error('搜索错误:', error);
        setSearchError(error instanceof Error ? error.message : String(error));
        // 如果搜索失败，则回退到常规搜索
        setIsVectorSearch(false);
        setIsLLMSearch(false);
      } finally {
        setSearchLoading(false);
      }
    }
  };

  // 处理查看详情
  const handleViewDetails = (program: ProgramData) => {
    setSelectedProgram(program);
    setModalVisible(true);
  };

  // 处理关闭模态框
  const handleCloseModal = () => {
    setModalVisible(false);
  };
  
  // 处理表格筛选和排序变化
  const handleTableChange = (
    newPagination: TablePaginationConfig,
    filters: Record<string, FilterValue | null>,
    sorter: any
  ) => {
    console.log("===== 表格事件触发 =====");
    console.log("分页:", newPagination);
    console.log("筛选条件:", filters);
    console.log("排序:", sorter);
    
    // 更新分页状态 - 只更新必要的字段，避免不必要的重新渲染
    if (newPagination.current !== pagination.current || 
        newPagination.pageSize !== pagination.pageSize) {
      console.log(`更新分页: current=${newPagination.current}, pageSize=${newPagination.pageSize}`);
      setPagination({
        current: newPagination.current,
        pageSize: newPagination.pageSize
      });
    }
    
    // 更新筛选状态 - 保留AI筛选模式标志
    const newFilteredInfo = FilterService.buildFilterStateFromTable(filters);
    const prevIsLLMSearch = isLLMSearch;
    
    // 只有当筛选条件真正改变时才更新状态
    if (JSON.stringify(newFilteredInfo) !== JSON.stringify(filteredInfo)) {
      console.log("筛选条件已更改，更新 filteredInfo");
      setFilteredInfo(newFilteredInfo);
    } else {
      console.log("筛选条件未变，保持 filteredInfo 不变");
    }
    
    // 处理排序
    if (sorter && 'field' in sorter) {
      const { field, order } = sorter;
      console.log(`更新排序: field=${field}, order=${order}`);
      setSortInfo({
        field: order ? field : null,
        order: order || null
      });
    } else {
      console.log("清除排序");
      setSortInfo({ field: null, order: null });
    }
    
    console.log("=========================");
  };
  
  // 清除所有筛选条件
  const clearAllFilters = () => {
    console.log("===== 清除所有筛选条件 =====");
    console.log("设置 filteredInfo = INITIAL_FILTER_STATE");
    setFilteredInfo(INITIAL_FILTER_STATE);
    setAiThinkingProcess('');
    // 清除AI搜索状态
    setIsLLMSearch(false);
    console.log("=============================");
  };
  
  // 移除单个筛选条件
  const removeFilter = (key: keyof FilterState, value: string) => {
    console.log(`===== 移除筛选条件: ${key}=${value} =====`);
    setFilteredInfo(prev => {
      const newState = {
        ...prev,
        [key]: prev[key].filter(v => v !== value)
      };
      console.log("新的筛选状态:", newState);
      return newState;
    });
    console.log("===============================");
  };

  // 生成表格列
  const columns = useMemo(() => 
    generateColumns(filterOptions, filteredInfo, handleViewDetails),
    [filterOptions, filteredInfo]
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 20px' }}>
        <Title level={3} style={{ margin: '16px 0' }}>新加坡管理学院(SIM)项目浏览</Title>
      </Header>
      <Content style={{ padding: '20px 50px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <SearchBar onSearch={handleSearch} />
          
          {searchError && (
            <div style={{ color: 'red', marginBottom: 16 }}>
              搜索错误: {searchError}
            </div>
          )}
          
          {isAIStreaming && (
            <div style={{ marginBottom: 16, padding: '10px', border: '1px solid #eee', borderRadius: '4px' }}>
              <Typography.Text strong>AI 正在分析您的需求: </Typography.Text>
              <Spin size="small" style={{ marginLeft: 8 }}/>
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '200px', overflowY: 'auto', marginTop: '8px', backgroundColor: '#f9f9f9', padding: '8px' }}>
                {aiThinkingProcess || "正在连接AI服务..."}
              </pre>
            </div>
          )}
          
          {searchWeights && !isAIStreaming && (
            <div style={{ marginBottom: 16 }}>
              <Typography.Text type="secondary">搜索权重:</Typography.Text>
              <Space size={[0, 8]} wrap style={{ marginLeft: 8 }}>
                {Object.entries(searchWeights)
                  .sort(([_, a], [__, b]) => b - a)
                  .map(([field, weight]) => (
                    <Tag key={field} color={weight > 3 ? 'blue' : weight > 2 ? 'green' : 'default'}>
                      {field}: {weight.toFixed(1)}
                    </Tag>
                  ))}
              </Space>
            </div>
          )}
          
          <FilterTags 
            filteredInfo={filteredInfo}
            onRemoveFilter={removeFilter}
            onClearAllFilters={clearAllFilters}
          />
          
          {(loading || searchLoading) ? (
            <div style={{ textAlign: 'center', margin: '50px 0' }}>
              <Spin size="large" />
            </div>
          ) : (
            <>
              <div style={{ marginBottom: 16 }}>
                找到 {filteredData.length} 个项目
                {isVectorSearch && <Tag color="blue" style={{ marginLeft: 8 }}>语义搜索</Tag>}
                {isLLMSearch && !isAIStreaming && <Tag color="purple" style={{ marginLeft: 8 }}>智能搜索 (AI推荐)</Tag>}
                {isLLMSearch && isAIStreaming && <Tag color="gold" style={{ marginLeft: 8 }}>AI 智能分析中...</Tag>}
              </div>
              
              {filteredData.length === 0 && !loading && !searchLoading && Object.values(filteredInfo).some(arr => arr.length > 0) && (
                <div style={{ marginBottom: 16, padding: '16px', backgroundColor: '#fffbe6', border: '1px solid #ffe58f', borderRadius: '4px' }}>
                  <Typography.Text strong>
                    没有找到符合所有筛选条件的项目。
                  </Typography.Text>
                  <div style={{ marginTop: 8 }}>
                    <Typography.Text>
                      您可以尝试：
                    </Typography.Text>
                    <ul style={{ margin: '8px 0', paddingLeft: 24 }}>
                      <li>移除一些筛选条件</li>
                      <li>修改搜索关键词</li>
                      <li>切换到不同的搜索模式</li>
                    </ul>
                    <Button type="primary" size="small" onClick={clearAllFilters}>
                      清除所有筛选条件
                    </Button>
                  </div>
                </div>
              )}
              
            <Table 
              columns={columns} 
              dataSource={filteredData} 
                rowKey={record => record.data_id.toString()}
                pagination={{
                  current: pagination.current,
                  pageSize: pagination.pageSize,
                  total: filteredData.length,
                  showSizeChanger: true,
                  showTotal: (total) => `共 ${total} 条记录`
                }}
                onChange={handleTableChange}
              scroll={{ x: 1500 }}
                showSorterTooltip={false}
            />
            </>
          )}
        </Space>
        
        <ProgramDetail 
          open={modalVisible}
          program={selectedProgram}
          onClose={handleCloseModal}
        />
      </Content>
    </Layout>
  );
};

export default App; 