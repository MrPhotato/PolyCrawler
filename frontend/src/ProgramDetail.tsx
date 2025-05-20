import React from 'react';
import { Modal, Typography, Descriptions, Collapse, List, Tag, Divider, Alert } from 'antd';
import { ProgramData } from './types';

const { Title, Paragraph } = Typography;
const { Panel } = Collapse;

interface ProgramDetailProps {
  open: boolean;
  program: ProgramData | null;
  onClose: () => void;
}

const ProgramDetail: React.FC<ProgramDetailProps> = ({ open, program, onClose }) => {
  if (!program) return null;

  return (
    <Modal
      title={program.program_name}
      open={open}
      onCancel={onClose}
      footer={null}
      width={800}
    >
      {/* 如果有 warning 字段，优先显示 */}
      {program.warning && (
        <Alert
          message="数据警告"
          description={program.warning}
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}
      <Typography>
      <Title level={4}>入学要求</Title>
        <Collapse defaultActiveKey={['1']}>
          <Panel header="国际学生入学要求" key="1">
            {program.admission_requirements.international.map((req, index) => (
              <div key={index} style={{ marginBottom: 16 }}>
                <Tag color="green">{req.requirement_type}</Tag>
                <Paragraph>{req.requirement_description}</Paragraph>
                {req.specific_requirements.length > 0 && (
                  <List
                    size="small"
                    bordered
                    dataSource={req.specific_requirements}
                    renderItem={item => (
                      <List.Item>
                        <strong>{item.requirement_type}:</strong> {item.grade > 0 ? `最低${item.grade}分` : ''} {item.requirement_description}
                      </List.Item>
                    )}
                  />
                )}
              </div>
            ))}
          </Panel>
          <Panel header="新加坡学生入学要求" key="2">
            {program.admission_requirements.domestic.map((req, index) => (
              <div key={index} style={{ marginBottom: 16 }}>
                <Tag color="blue">{req.requirement_type}</Tag>
                <Paragraph>{req.requirement_description}</Paragraph>
                {req.specific_requirements.length > 0 && (
                  <List
                    size="small"
                    bordered
                    dataSource={req.specific_requirements}
                    renderItem={item => (
                      <List.Item>
                        <strong>{item.requirement_type}:</strong> {item.grade > 0 ? `最低${item.grade}分` : ''} {item.requirement_description}
                      </List.Item>
                    )}
                  />
                )}
              </div>
            ))}
          </Panel>
        </Collapse>

        <Divider />
        
        <Descriptions title="基本信息" bordered column={1}>
          <Descriptions.Item label="发证学校">{program.university}</Descriptions.Item>
          <Descriptions.Item label="学科">{program.discipline}</Descriptions.Item>
          <Descriptions.Item label="子学科">{program.sub_discipline}</Descriptions.Item>
          <Descriptions.Item label="标签">{program.tags}</Descriptions.Item>
          <Descriptions.Item label="学业阶段">{program.academic_level}</Descriptions.Item>
          <Descriptions.Item label="项目类型">{program.programme_type}</Descriptions.Item>
          <Descriptions.Item label="申请日期">{program.application_dates}</Descriptions.Item>
          <Descriptions.Item label="新加坡学生费用">
            S${program.domestic_total_fee.fee_lower.toLocaleString()} - S${program.domestic_total_fee.fee_upper.toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="国际学生费用">
            S${program.international_total_fee.fee_lower.toLocaleString()} - S${program.international_total_fee.fee_upper.toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="官方链接">
            <a href={program.program_link} target="_blank" rel="noopener noreferrer">
              {program.program_link}
            </a>
          </Descriptions.Item>
        </Descriptions>

        <Divider />
        
        <Title level={4}>项目介绍</Title>
        <Paragraph>
          {program.introduction.split('\n').map((paragraph, index) => (
            <Paragraph key={index}>{paragraph}</Paragraph>
          ))}
        </Paragraph>

        <Divider />
        
        <Title level={4}>课程模块</Title>
        <Collapse>
          {program.course_modules.map((module, index) => (
            <Panel header={module.module_name} key={String(index)}>
              <List
                size="small"
                bordered
                dataSource={module.course_modules}
                renderItem={course => (
                  <List.Item>
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                      <strong>{course.course_name}</strong>
                      <span>{course.course_description}</span>
                    </div>
                  </List.Item>
                )}
              />
            </Panel>
          ))}
        </Collapse>
      </Typography>
    </Modal>
  );
};

export default ProgramDetail; 