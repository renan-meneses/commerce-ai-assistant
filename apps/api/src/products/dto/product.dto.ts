import { Injectable } from '@nestjs/common';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import {
  IsArray,
  IsBoolean,
  IsInt,
  IsNumber,
  IsOptional,
  IsString,
  IsUUID,
  MaxLength,
  Min,
  MinLength,
} from 'class-validator';

export class CreateProductDto {
  @ApiProperty({ example: 'NB-ASUS-VIVO-16' })
  @IsString()
  @MinLength(2)
  @MaxLength(40)
  sku!: string;

  @ApiProperty({ example: 'ASUS Vivobook 16X' })
  @IsString()
  @MinLength(2)
  @MaxLength(200)
  name!: string;

  @ApiProperty({ example: 'Notebook with 16 GB RAM and Ryzen 7...' })
  @IsString()
  @MinLength(10)
  description!: string;

  @ApiProperty({ example: '4d2f0f0e-...' })
  @IsUUID()
  categoryId!: string;

  @ApiProperty({ example: 'ASUS' })
  @IsString()
  @MinLength(1)
  brand!: string;

  @ApiProperty({ example: 489900, description: 'Price in cents' })
  @IsInt()
  @Min(0)
  priceCents!: number;

  @ApiPropertyOptional({
    example: {
      processor: 'Ryzen 7 5800H',
      ram: '16 GB DDR4',
      storage: '512 GB NVMe SSD',
      screen: '16" WUXGA',
      gpu: 'RTX 3050',
      weight: '1.9 kg',
    },
  })
  @IsOptional()
  specifications?: Record<string, string>;
}

export class UpdateProductDto {
  @ApiPropertyOptional({ example: 'ASUS Vivobook 16X (2025)' })
  @IsOptional()
  @IsString()
  @MinLength(2)
  @MaxLength(200)
  name?: string;

  @ApiPropertyOptional({ example: 'Updated description' })
  @IsOptional()
  @IsString()
  @MinLength(10)
  description?: string;

  @ApiPropertyOptional({ example: 529900 })
  @IsOptional()
  @IsInt()
  @Min(0)
  priceCents?: number;

  @ApiPropertyOptional({ example: true })
  @IsOptional()
  @IsBoolean()
  active?: boolean;

  @ApiPropertyOptional({ example: { ram: '32 GB DDR5' } })
  @IsOptional()
  specifications?: Record<string, string>;
}

export class ListProductsQuery {
  @ApiPropertyOptional({ example: 'notebook' })
  @IsOptional()
  @IsString()
  q?: string;

  @ApiPropertyOptional({ example: 'notebooks' })
  @IsOptional()
  @IsString()
  category?: string;

  @ApiPropertyOptional({ example: 'ASUS' })
  @IsOptional()
  @IsString()
  brand?: string;

  @ApiPropertyOptional({ example: 100000 })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  minPriceCents?: number;

  @ApiPropertyOptional({ example: 600000 })
  @IsOptional()
  @Type(() => Number)
  @IsNumber()
  @Min(0)
  maxPriceCents?: number;

  @ApiPropertyOptional({ example: 1 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page?: number = 1;

  @ApiPropertyOptional({ example: 20 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @IsNumber()
  limit?: number = 20;

  @ApiPropertyOptional({ example: 'priceCents' })
  @IsOptional()
  @IsString()
  sortBy?: string = 'name';

  @ApiPropertyOptional({ example: 'asc' })
  @IsOptional()
  @IsString()
  order?: 'asc' | 'desc' = 'asc';
}
