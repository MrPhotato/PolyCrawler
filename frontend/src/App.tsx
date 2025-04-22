import React, { useState, useEffect } from 'react';
import { Table, Layout, Typography, Input, Space, Spin, Button } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { ProgramData } from './types';
import ProgramDetail from './ProgramDetail';

const { Header, Content } = Layout;
const { Title } = Typography;
const { Search } = Input;

const App: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [data, setData] = useState<ProgramData[]>([]);
  const [filteredData, setFilteredData] = useState<ProgramData[]>([]);
  const [searchText, setSearchText] = useState<string>('');
  const [selectedProgram, setSelectedProgram] = useState<ProgramData | null>(null);
  const [modalVisible, setModalVisible] = useState<boolean>(false);

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

  useEffect(() => {
    if (searchText) {
      const filtered = data.filter(program => 
        program.program_name.toLowerCase().includes(searchText.toLowerCase()) || 
        program.university.toLowerCase().includes(searchText.toLowerCase()) ||
        program.discipline.toLowerCase().includes(searchText.toLowerCase())
      );
      setFilteredData(filtered);
    } else {
      setFilteredData(data);
    }
  }, [searchText, data]);

  const handleSearch = (value: string) => {
    setSearchText(value);
  };

  const handleViewDetails = (program: ProgramData) => {
    setSelectedProgram(program);
    setModalVisible(true);
  };

  const handleCloseModal = () => {
    setModalVisible(false);
  };

  const columns: ColumnsType<ProgramData> = [
    {
      title: '项目名称',
      dataIndex: 'program_name',
      key: 'program_name',
      sorter: (a, b) => a.program_name.localeCompare(b.program_name),
    },
    {
      title: '大学',
      dataIndex: 'university',
      key: 'university',
      sorter: (a, b) => a.university.localeCompare(b.university),
    },
    {
      title: '学科',
      dataIndex: 'discipline',
      key: 'discipline',
      sorter: (a, b) => a.discipline.localeCompare(b.discipline),
    },
    {
      title: '子学科',
      dataIndex: 'sub_discipline',
      key: 'sub_discipline',
      sorter: (a, b) => a.sub_discipline.localeCompare(b.sub_discipline),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
    },
    {
      title: '学术水平',
      dataIndex: 'academic_level',
      key: 'academic_level',
    },
    {
      title: '项目类型',
      dataIndex: 'programme_type',
      key: 'programme_type',
    },
    {
      title: '国内费用区间',
      key: 'domestic_fee',
      render: (_, record) => (
        <span>
          S${record.domestic_total_fee.fee_lower.toLocaleString()} - S${record.domestic_total_fee.fee_upper.toLocaleString()}
        </span>
      ),
      sorter: (a, b) => a.domestic_total_fee.fee_lower - b.domestic_total_fee.fee_lower,
    },
    {
      title: '国际费用区间',
      key: 'international_fee',
      render: (_, record) => (
        <span>
          S${record.international_total_fee.fee_lower.toLocaleString()} - S${record.international_total_fee.fee_upper.toLocaleString()}
        </span>
      ),
      sorter: (a, b) => a.international_total_fee.fee_lower - b.international_total_fee.fee_lower,
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

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 20px' }}>
        <Title level={3} style={{ margin: '16px 0' }}>新加坡管理学院(SIM)项目浏览</Title>
      </Header>
      <Content style={{ padding: '20px 50px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Search
            placeholder="搜索项目名称、大学或学科"
            allowClear
            enterButton="搜索"
            size="large"
            onSearch={handleSearch}
            style={{ marginBottom: 20 }}
          />
          
          {loading ? (
            <div style={{ textAlign: 'center', margin: '50px 0' }}>
              <Spin size="large" />
            </div>
          ) : (
            <Table 
              columns={columns} 
              dataSource={filteredData} 
              rowKey="data_id"
              pagination={{ pageSize: 10 }}
              scroll={{ x: 1500 }}
            />
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