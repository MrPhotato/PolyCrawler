import React, { useState, useEffect } from 'react';
import { Input, AutoComplete, Space, Tag, Typography, Radio, Tooltip, Button, Popover, message } from 'antd';
import { SearchOutlined, AimOutlined, RobotOutlined } from '@ant-design/icons';
import { debounce } from 'lodash';

const { Search } = Input;

interface SearchBarProps {
  onSearch: (value: string, useVectorSearch?: boolean, useLLMSearch?: boolean) => void;
  placeholder?: string;
}

const SearchBar: React.FC<SearchBarProps> = ({ 
  onSearch, 
  placeholder = "搜索项目名称、发证大学或学科" 
}) => {
  const [searchValue, setSearchValue] = useState<string>('');
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [searchMode, setSearchMode] = useState<'keyword' | 'vector' | 'llm'>('keyword');
  
  // 从本地存储加载搜索历史
  useEffect(() => {
    const savedHistory = localStorage.getItem('searchHistory');
    if (savedHistory) {
      setSearchHistory(JSON.parse(savedHistory));
    }
  }, []);

  // 防抖处理搜索输入
  const debouncedSearch = debounce((value: string) => {
    onSearch(value, searchMode === 'vector', searchMode === 'llm');
  }, 300);

  // 处理搜索输入变化
  const handleSearchChange = (value: string) => {
    setSearchValue(value);
    // 只在非智能搜索模式下使用防抖自动搜索
    if (searchMode !== 'llm') {
      debouncedSearch(value);
    }
  };

  // 处理搜索提交
  const handleSearchSubmit = (value: string) => {
    // 保存搜索历史
    if (value && !searchHistory.includes(value)) {
      const newHistory = [value, ...searchHistory].slice(0, 10);
      localStorage.setItem('searchHistory', JSON.stringify(newHistory));
      setSearchHistory(newHistory);
    }
    onSearch(value, searchMode === 'vector', searchMode === 'llm');
  };

  // 点击历史记录标签
  const handleHistoryTagClick = (value: string) => {
    setSearchValue(value);
    onSearch(value, searchMode === 'vector', searchMode === 'llm');
  };

  // 清除历史记录
  const clearSearchHistory = () => {
    localStorage.removeItem('searchHistory');
    setSearchHistory([]);
  };

  // 切换搜索模式
  const handleSearchModeChange = (e: any) => {
    const newMode = e.target.value;
    setSearchMode(newMode);
    // 只在非智能搜索模式下才立即执行搜索
    if (searchValue && newMode !== 'llm') {
      onSearch(searchValue, newMode === 'vector', newMode === 'llm');
    }
  };

  return (
    <div className="search-container">
      <div style={{ display: 'flex', marginBottom: 16 }}>
        <Search
          placeholder={searchMode === 'llm' ? "输入后请点击搜索按钮或按回车" : placeholder}
          allowClear
          enterButton="搜索"
          size="large"
          value={searchValue}
          onChange={(e) => handleSearchChange(e.target.value)}
          onSearch={handleSearchSubmit}
          style={{ flex: 1 }}
          prefix={
            searchMode === 'vector' ? <AimOutlined /> : 
            searchMode === 'llm' ? <RobotOutlined /> :
            <SearchOutlined />
          }
        />
        <div style={{ marginLeft: 16, display: 'flex', alignItems: 'center' }}>
          <Radio.Group 
            value={searchMode} 
            onChange={handleSearchModeChange}
            buttonStyle="solid"
          >
            <Tooltip title="使用关键词匹配搜索">
              <Radio.Button value="keyword">关键词搜索</Radio.Button>
            </Tooltip>
            <Tooltip title="使用语义向量搜索，更好地理解搜索意图">
              <Radio.Button value="vector">语义搜索</Radio.Button>
            </Tooltip>
            <Tooltip title="使用LLM动态调整权重的智能搜索。请输入后点击搜索按钮或按回车搜索。">
              <Radio.Button value="llm">智能搜索</Radio.Button>
            </Tooltip>
          </Radio.Group>
        </div>
      </div>
      
      {searchHistory.length > 0 && (
        <div className="search-history" style={{ marginBottom: 16 }}>
          <Space size={[0, 8]} wrap>
            <Typography.Text type="secondary">搜索历史：</Typography.Text>
            {searchHistory.map(item => (
              <Tag 
                key={item} 
                onClick={() => handleHistoryTagClick(item)}
                style={{ cursor: 'pointer' }}
              >
                {item}
              </Tag>
            ))}
            <Typography.Link onClick={clearSearchHistory}>
              清除历史
            </Typography.Link>
          </Space>
        </div>
      )}
    </div>
  );
};

export default SearchBar; 