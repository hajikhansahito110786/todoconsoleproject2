import { Field, ID } from '@sqlmodel/core';
import { SQLModel } from '@sqlmodel/core/sqlmodel';

export class Student extends SQLModel {
  @Field({ type: 'text', nullable: false })
  name!: string;

  @Field({ type: 'text', nullable: false, unique: true })
  email!: string;

  @Field({ type: 'integer', nullable: true })
  age?: number;

  @Field({ type: 'text', nullable: true })
  grade?: string;
}

// Initialize the model
Student.init({
  tableName: 'students',
});