export interface ProgramData {
  data_id: number;
  program_name: string;
  university: string;
  discipline: string;
  sub_discipline: string;
  tags: string;
  academic_level: string;
  programme_type: string;
  application_dates: string;
  fee_range: string;
  program_link: string;
  introduction: string;
  domestic_total_fee: {
    fee_lower: number;
    fee_upper: number;
  };
  international_total_fee: {
    fee_lower: number;
    fee_upper: number;
  };
  admission_requirements: {
    international: Requirement[];
    domestic: Requirement[];
  };
  course_modules: Module[];
  warning?: string;
}

export interface Requirement {
  requirement_type: string;
  requirement_description: string;
  specific_requirements: SpecificRequirement[];
}

export interface SpecificRequirement {
  requirement_type: string;
  grade: number;
  requirement_description: string;
}

export interface Module {
  module_name: string;
  course_modules: CourseModule[];
}

export interface CourseModule {
  course_name: string;
  course_description: string;
} 