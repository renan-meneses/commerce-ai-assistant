import { ApiProperty } from '@nestjs/swagger';
import { IsEmail, IsString, MinLength } from 'class-validator';

export class RegisterDto {
  @ApiProperty({ example: 'maria@example.com' })
  @IsEmail()
  email!: string;

  @ApiProperty({ example: 'Maria Silva' })
  @IsString()
  @MinLength(2)
  name!: string;

  @ApiProperty({ example: 's3cret-pass' })
  @IsString()
  @MinLength(8)
  password!: string;
}

export class LoginDto {
  @ApiProperty({ example: 'maria@example.com' })
  @IsEmail()
  email!: string;

  @ApiProperty({ example: 's3cret-pass' })
  @IsString()
  password!: string;
}
