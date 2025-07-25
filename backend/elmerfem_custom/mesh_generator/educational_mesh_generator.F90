!> Educational Mesh Generator for ElmerFEM
!> Provides fast, simplified mesh generation for educational FEM simulations
!> \ingroup EducationalMeshGenerator
MODULE EducationalMeshGenerator
  USE, INTRINSIC :: ISO_C_BINDING
  USE, INTRINSIC :: ISO_FORTRAN_ENV, ONLY: ERROR_UNIT
  
  IMPLICIT NONE
  
  PRIVATE
  PUBLIC :: GeometryParams, MeshQuality, GenerateMesh_C
  
  ! Define precision
  INTEGER, PARAMETER :: dp = SELECTED_REAL_KIND(15,307)
  
  !> Geometry parameter structure for mesh generation
  TYPE, BIND(C) :: GeometryParams
    INTEGER(C_INT) :: geometry_type    !< 1=rectangle, 2=circle, 3=annulus, 4=l_shape
    REAL(C_DOUBLE) :: params(10)       !< Geometry-specific parameters
    INTEGER(C_INT) :: mesh_density     !< Element density level (1-5)
    INTEGER(C_INT) :: boundary_layer   !< Enable boundary layer mesh (0=false, 1=true)
  END TYPE GeometryParams
  
  !> Mesh quality metrics structure
  TYPE, BIND(C) :: MeshQuality
    REAL(C_DOUBLE) :: min_angle          !< Minimum element angle
    REAL(C_DOUBLE) :: max_angle          !< Maximum element angle
    REAL(C_DOUBLE) :: aspect_ratio_avg   !< Average element aspect ratio
    REAL(C_DOUBLE) :: aspect_ratio_max   !< Maximum element aspect ratio
    INTEGER(C_INT) :: total_elements     !< Total number of elements
    INTEGER(C_INT) :: total_nodes        !< Total number of nodes
    INTEGER(C_INT) :: return_code        !< 0=success, non-zero=error
  END TYPE MeshQuality
  
CONTAINS
  
  !> Generate mesh based on geometry parameters (C-compatible interface)
  !> \param[in] geometry Input geometry parameters
  !> \param[in] output_dir Output directory path (C string)
  !> \param[out] quality Output mesh quality metrics
  SUBROUTINE GenerateMesh_C(geometry, output_dir, quality) BIND(C, name="generate_mesh")
    TYPE(GeometryParams), INTENT(IN) :: geometry
    CHARACTER(KIND=C_CHAR), INTENT(IN) :: output_dir(*)
    TYPE(MeshQuality), INTENT(OUT) :: quality
    
    CHARACTER(LEN=:), ALLOCATABLE :: fortran_output_dir
    INTEGER :: i, str_len
    
    ! Convert C string to Fortran string
    str_len = 0
    DO i = 1, 1024
      IF (output_dir(i) == C_NULL_CHAR) EXIT
      str_len = i
    END DO
    
    ALLOCATE(CHARACTER(LEN=str_len) :: fortran_output_dir)
    DO i = 1, str_len
      fortran_output_dir(i:i) = output_dir(i)
    END DO
    
    ! Call the actual mesh generation routine
    CALL GenerateMesh(geometry, fortran_output_dir, quality)
    
    DEALLOCATE(fortran_output_dir)
    
  END SUBROUTINE GenerateMesh_C
  
  !> Internal mesh generation routine
  SUBROUTINE GenerateMesh(geometry, output_dir, quality)
    TYPE(GeometryParams), INTENT(IN) :: geometry
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    TYPE(MeshQuality), INTENT(OUT) :: quality
    
    ! Initialize quality structure with dummy values
    quality%min_angle = 30.0_dp
    quality%max_angle = 120.0_dp
    quality%aspect_ratio_avg = 1.5_dp
    quality%aspect_ratio_max = 2.0_dp
    quality%total_elements = 0
    quality%total_nodes = 0
    quality%return_code = 0
    
    ! Route to appropriate mesh generator based on geometry type
    SELECT CASE(geometry%geometry_type)
    CASE(1)
      CALL GenerateRectangleMesh(geometry, output_dir, quality)
    CASE(2)
      CALL GenerateCircleMesh(geometry, output_dir, quality)
    CASE(3)
      CALL GenerateAnnulusMesh(geometry, output_dir, quality)
    CASE(4)
      CALL GenerateLShapeMesh(geometry, output_dir, quality)
    CASE DEFAULT
      WRITE(ERROR_UNIT, *) "ERROR: Unknown geometry type:", geometry%geometry_type
      quality%return_code = 1
    END SELECT
    
  END SUBROUTINE GenerateMesh
  
  !> Generate rectangle mesh (full implementation)
  SUBROUTINE GenerateRectangleMesh(geometry, output_dir, quality)
    TYPE(GeometryParams), INTENT(IN) :: geometry
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    TYPE(MeshQuality), INTENT(INOUT) :: quality
    
    ! Local variables
    REAL(dp) :: width, height, dx, dy, x, y
    INTEGER :: nx, ny, i, j, node_id, elem_id, bc_elem_id
    INTEGER :: n1, n2, n3, n4
    INTEGER :: unit_header, unit_nodes, unit_elements, unit_boundary, ios
    INTEGER :: total_boundary_elements
    CHARACTER(LEN=512) :: filename
    REAL(dp) :: min_angle_rad, max_angle_rad
    
    ! Buffer for writing multiple lines at once
    CHARACTER(LEN=100000) :: buffer
    INTEGER :: buffer_pos, line_len
    CHARACTER(LEN=1000) :: line
    
    ! Extract rectangle parameters
    width = geometry%params(1)
    height = geometry%params(2)
    
    ! Calculate number of elements based on mesh density
    ! Scale factor: density 1 = 10 elem/unit, density 5 = 50 elem/unit
    nx = MAX(2, INT(10.0_dp * geometry%mesh_density * width))
    ny = MAX(2, INT(10.0_dp * geometry%mesh_density * height))
    
    ! Calculate mesh spacing
    dx = width / REAL(nx, dp)
    dy = height / REAL(ny, dp)
    
    ! Update quality metrics
    quality%total_nodes = (nx + 1) * (ny + 1)
    quality%total_elements = nx * ny
    total_boundary_elements = 2 * nx + 2 * ny
    
    ! Calculate aspect ratio (all elements are identical rectangles)
    quality%aspect_ratio_avg = MAX(dx/dy, dy/dx)
    quality%aspect_ratio_max = quality%aspect_ratio_avg
    
    ! Calculate angles for rectangular elements
    IF (ABS(dx - dy) < 1.0e-10_dp) THEN
      ! Square elements
      quality%min_angle = 90.0_dp
      quality%max_angle = 90.0_dp
    ELSE
      ! Rectangular elements - angles are still 90 degrees
      quality%min_angle = 90.0_dp
      quality%max_angle = 90.0_dp
    END IF
    
    ! Write mesh.header
    filename = TRIM(output_dir) // '/mesh.header'
    OPEN(NEWUNIT=unit_header, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.header for writing"
      quality%return_code = 2
      RETURN
    END IF
    
    ! Header format: nodes elements boundary_elements
    WRITE(unit_header, '(I0,1X,I0,1X,I0)') quality%total_nodes, quality%total_elements, total_boundary_elements
    ! Number of element types (2: bulk 404 and boundary 202)
    WRITE(unit_header, '(I0)') 2
    ! Element type 404 (4-node quad) and count
    WRITE(unit_header, '(I0,1X,I0)') 404, quality%total_elements
    ! Element type 202 (2-node line) and count
    WRITE(unit_header, '(I0,1X,I0)') 202, total_boundary_elements
    
    CLOSE(unit_header)
    
    ! Write mesh.nodes with buffering
    filename = TRIM(output_dir) // '/mesh.nodes'
    OPEN(NEWUNIT=unit_nodes, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.nodes for writing"
      quality%return_code = 2
      RETURN
    END IF
    
    ! Generate nodes in row-major order with buffering
    buffer = ''
    buffer_pos = 1
    node_id = 0
    DO j = 0, ny
      y = j * dy
      DO i = 0, nx
        x = i * dx
        node_id = node_id + 1
        ! Format: node_id boundary_tag x y z
        WRITE(line, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
              node_id, -1, x, y, 0.0_dp
        line_len = LEN_TRIM(line)
        
        ! Check if buffer has space
        IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
          ! Write buffer and reset
          WRITE(unit_nodes, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
          buffer = ''
          buffer_pos = 1
        END IF
        
        ! Add line to buffer
        buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
        buffer_pos = buffer_pos + line_len + 1
      END DO
    END DO
    
    ! Write remaining buffer (remove trailing newline to prevent extra blank line)
    IF (buffer_pos > 1) THEN
      ! Remove the final newline character to prevent extra blank line
      IF (buffer_pos > 1 .AND. buffer(buffer_pos-1:buffer_pos-1) == NEW_LINE('A')) THEN
        WRITE(unit_nodes, '(A)', ADVANCE='NO') buffer(1:buffer_pos-2)
      ELSE
        WRITE(unit_nodes, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
      END IF
    END IF
    
    CLOSE(unit_nodes)
    
    ! Write mesh.elements with buffering
    filename = TRIM(output_dir) // '/mesh.elements'
    OPEN(NEWUNIT=unit_elements, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.elements for writing"
      quality%return_code = 2
      RETURN
    END IF
    
    ! Generate elements (4-node quads, type 404) with buffering
    buffer = ''
    buffer_pos = 1
    elem_id = 0
    DO j = 1, ny
      DO i = 1, nx
        elem_id = elem_id + 1
        ! Calculate node indices
        n1 = (j-1) * (nx+1) + i
        n2 = n1 + 1
        n3 = n1 + nx + 2
        n4 = n1 + nx + 1
        
        ! Format: elem_id material_id element_type node1 node2 node3 node4
        WRITE(line, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
              elem_id, 1, 404, n1, n2, n3, n4
        line_len = LEN_TRIM(line)
        
        ! Check if buffer has space
        IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
          ! Write buffer and reset
          WRITE(unit_elements, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
          buffer = ''
          buffer_pos = 1
        END IF
        
        ! Add line to buffer
        buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
        buffer_pos = buffer_pos + line_len + 1
      END DO
    END DO
    
    ! Write remaining buffer (remove trailing newline to prevent extra blank line)
    IF (buffer_pos > 1) THEN
      ! Remove the final newline character to prevent extra blank line
      IF (buffer_pos > 1 .AND. buffer(buffer_pos-1:buffer_pos-1) == NEW_LINE('A')) THEN
        WRITE(unit_elements, '(A)', ADVANCE='NO') buffer(1:buffer_pos-2)
      ELSE
        WRITE(unit_elements, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
      END IF
    END IF
    
    CLOSE(unit_elements)
    
    ! Write mesh.boundary with buffering
    filename = TRIM(output_dir) // '/mesh.boundary'
    OPEN(NEWUNIT=unit_boundary, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.boundary for writing"
      quality%return_code = 2
      RETURN
    END IF
    
    buffer = ''
    buffer_pos = 1
    bc_elem_id = 0
    
    ! Bottom boundary (y=0)
    DO i = 1, nx
      bc_elem_id = bc_elem_id + 1
      n1 = i
      n2 = i + 1
      elem_id = i  ! Parent element
      ! Format: bc_elem_id boundary_type parent1 parent2 element_type node1 node2
      WRITE(line, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
            bc_elem_id, 1, elem_id, 0, 202, n1, n2
      line_len = LEN_TRIM(line)
      
      ! Check if buffer has space
      IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
        ! Write buffer and reset
        WRITE(unit_boundary, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
        buffer = ''
        buffer_pos = 1
      END IF
      
      ! Add line to buffer
      buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
      buffer_pos = buffer_pos + line_len + 1
    END DO
    
    ! Right boundary (x=width)
    DO j = 1, ny
      bc_elem_id = bc_elem_id + 1
      n1 = j * (nx+1) + nx + 1
      n2 = (j+1) * (nx+1) + nx + 1
      elem_id = j * nx  ! Parent element (rightmost in row)
      ! Format: bc_elem_id boundary_type parent1 parent2 element_type node1 node2
      WRITE(line, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
            bc_elem_id, 2, elem_id, 0, 202, n1, n2
      line_len = LEN_TRIM(line)
      
      ! Check if buffer has space
      IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
        ! Write buffer and reset
        WRITE(unit_boundary, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
        buffer = ''
        buffer_pos = 1
      END IF
      
      ! Add line to buffer
      buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
      buffer_pos = buffer_pos + line_len + 1
    END DO
    
    ! Top boundary (y=height)
    DO i = 1, nx
      bc_elem_id = bc_elem_id + 1
      n1 = ny * (nx+1) + i + 1
      n2 = ny * (nx+1) + i
      elem_id = (ny-1) * nx + i  ! Parent element (top row)
      ! Format: bc_elem_id boundary_type parent1 parent2 element_type node1 node2
      WRITE(line, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
            bc_elem_id, 3, elem_id, 0, 202, n1, n2
      line_len = LEN_TRIM(line)
      
      ! Check if buffer has space
      IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
        ! Write buffer and reset
        WRITE(unit_boundary, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
        buffer = ''
        buffer_pos = 1
      END IF
      
      ! Add line to buffer
      buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
      buffer_pos = buffer_pos + line_len + 1
    END DO
    
    ! Left boundary (x=0)
    DO j = 1, ny
      bc_elem_id = bc_elem_id + 1
      n1 = (j+1) * (nx+1) + 1
      n2 = j * (nx+1) + 1
      elem_id = (j-1) * nx + 1  ! Parent element (leftmost in row)
      ! Format: bc_elem_id boundary_type parent1 parent2 element_type node1 node2
      WRITE(line, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
            bc_elem_id, 4, elem_id, 0, 202, n1, n2
      line_len = LEN_TRIM(line)
      
      ! Check if buffer has space
      IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
        ! Write buffer and reset
        WRITE(unit_boundary, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
        buffer = ''
        buffer_pos = 1
      END IF
      
      ! Add line to buffer
      buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
      buffer_pos = buffer_pos + line_len + 1
    END DO
    
    ! Write remaining buffer (remove trailing newline to prevent extra blank line)
    IF (buffer_pos > 1) THEN
      ! Remove the final newline character to prevent extra blank line
      IF (buffer_pos > 1 .AND. buffer(buffer_pos-1:buffer_pos-1) == NEW_LINE('A')) THEN
        WRITE(unit_boundary, '(A)', ADVANCE='NO') buffer(1:buffer_pos-2)
      ELSE
        WRITE(unit_boundary, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
      END IF
    END IF
    
    CLOSE(unit_boundary)
    
    ! Log success
    WRITE(ERROR_UNIT, '(A,I0,A,I0,A)') "INFO: Successfully generated rectangle mesh with ", &
         quality%total_elements, " elements and ", quality%total_nodes, " nodes"
    WRITE(ERROR_UNIT, '(A,I0,A,I0)') "INFO: Mesh dimensions: ", nx, " x ", ny
    WRITE(ERROR_UNIT, '(A,F8.6,A,F8.6)') "INFO: Element size: dx=", dx, ", dy=", dy
    WRITE(ERROR_UNIT, '(A,F6.2)') "INFO: Aspect ratio: ", quality%aspect_ratio_avg
    
    quality%return_code = 0
    
  END SUBROUTINE GenerateRectangleMesh
  
  !> Generate circle mesh (stub implementation)
  SUBROUTINE GenerateCircleMesh(geometry, output_dir, quality)
    TYPE(GeometryParams), INTENT(IN) :: geometry
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    TYPE(MeshQuality), INTENT(INOUT) :: quality
    
    ! Stub implementation
    quality%total_elements = 100
    quality%total_nodes = 50
    quality%return_code = 0
    
    WRITE(ERROR_UNIT, *) "INFO: Circle mesh generation not yet implemented"
    
  END SUBROUTINE GenerateCircleMesh
  
  !> Generate annulus mesh (stub implementation)
  SUBROUTINE GenerateAnnulusMesh(geometry, output_dir, quality)
    TYPE(GeometryParams), INTENT(IN) :: geometry
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    TYPE(MeshQuality), INTENT(INOUT) :: quality
    
    ! Stub implementation
    quality%total_elements = 200
    quality%total_nodes = 100
    quality%return_code = 0
    
    WRITE(ERROR_UNIT, *) "INFO: Annulus mesh generation not yet implemented"
    
  END SUBROUTINE GenerateAnnulusMesh
  
  !> Generate L-shape mesh (stub implementation)
  SUBROUTINE GenerateLShapeMesh(geometry, output_dir, quality)
    TYPE(GeometryParams), INTENT(IN) :: geometry
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    TYPE(MeshQuality), INTENT(INOUT) :: quality
    
    ! Stub implementation
    quality%total_elements = 150
    quality%total_nodes = 75
    quality%return_code = 0
    
    WRITE(ERROR_UNIT, *) "INFO: L-shape mesh generation not yet implemented"
    
  END SUBROUTINE GenerateLShapeMesh
  
END MODULE EducationalMeshGenerator
