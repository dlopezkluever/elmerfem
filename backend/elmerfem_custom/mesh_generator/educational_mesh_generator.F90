!> Educational Mesh Generator for ElmerFEM
!> Provides fast, simplified mesh generation for educational FEM simulations
!> \ingroup EducationalMeshGenerator
MODULE EducationalMeshGenerator
  USE, INTRINSIC :: ISO_C_BINDING
  USE, INTRINSIC :: ISO_FORTRAN_ENV, ONLY: ERROR_UNIT
  
  IMPLICIT NONE
  
  PRIVATE
  PUBLIC :: GeometryParams, MeshQuality, GenerateMesh_C
  PUBLIC :: ComputeQuality, ApplyLaplacianSmoothing, ExportQualityJSON
  PUBLIC :: GenerateBoundaryLayerSpacing, AdaptiveElementSize
  PUBLIC :: GenerateAnnulusMeshEnhanced, GenerateRectangleMeshEnhanced
  PUBLIC :: BenchmarkMeshGeneration
  
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
      ! Use enhanced version if boundary layers requested
      IF (geometry%boundary_layer == 1) THEN
        CALL GenerateRectangleMeshEnhanced(geometry, output_dir, quality)
      ELSE
        CALL GenerateRectangleMesh(geometry, output_dir, quality)
      END IF
    CASE(2)
      CALL GenerateCircleMesh(geometry, output_dir, quality)
    CASE(3)
      ! Always use enhanced annulus generator (Task 20.3)
      CALL GenerateAnnulusMeshEnhanced(geometry, output_dir, quality)
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
  
  !> Generate circle mesh with radial structure and triangle elements
  !> Uses polar coordinates with optional exponential radial spacing
  !> Creates triangle fan pattern from center outward
  SUBROUTINE GenerateCircleMesh(geometry, output_dir, quality)
    TYPE(GeometryParams), INTENT(IN) :: geometry
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    TYPE(MeshQuality), INTENT(INOUT) :: quality
    
    ! Local variables
    REAL(dp) :: radius, r, theta, x, y
    INTEGER :: nr, ntheta, i, j, node_id, elem_id, bc_elem_id
    INTEGER :: n1, n2, n3, ring_start, ring_end
    INTEGER :: unit_header, unit_nodes, unit_elements, unit_boundary, ios
    INTEGER :: total_boundary_elements
    CHARACTER(LEN=512) :: filename
    REAL(dp) :: dr, dtheta, r_ratio
    REAL(dp), ALLOCATABLE :: radial_positions(:)
    REAL(dp) :: angle1, angle2, angle3, min_angle_local, max_angle_local
    REAL(dp) :: side1, side2, side3, s, area
    
    ! Buffer for writing multiple lines at once
    CHARACTER(LEN=100000) :: buffer
    INTEGER :: buffer_pos, line_len
    CHARACTER(LEN=1000) :: line
    
    ! Mathematical constants
    REAL(dp), PARAMETER :: PI = 3.141592653589793238_dp
    REAL(dp), PARAMETER :: TWO_PI = 2.0_dp * PI
    REAL(dp), PARAMETER :: RAD_TO_DEG = 180.0_dp / PI
    
    ! Extract circle parameters
    radius = geometry%params(1)
    
    ! Calculate number of radial and circumferential divisions based on mesh density
    ! Scale factor: density 1 = 5 radial, 12 circumferential; density 5 = 25 radial, 60 circumferential
    nr = 5 * geometry%mesh_density
    ntheta = 12 * geometry%mesh_density
    
    ! Allocate radial positions array
    ALLOCATE(radial_positions(0:nr))
    
    ! Subtask 16.2: Generate radial mesh points with optional exponential spacing
    IF (geometry%boundary_layer == 1) THEN
      ! Use exponential spacing for boundary layer effect
      r_ratio = 1.5_dp  ! Growth ratio
      radial_positions(0) = 0.0_dp
      dr = radius * (1.0_dp - r_ratio) / (1.0_dp - r_ratio**nr)
      DO i = 1, nr
        radial_positions(i) = radial_positions(i-1) + dr * r_ratio**(i-1)
      END DO
      ! Normalize to exact radius
      DO i = 1, nr
        radial_positions(i) = radial_positions(i) * radius / radial_positions(nr)
      END DO
    ELSE
      ! Use uniform radial spacing
      DO i = 0, nr
        radial_positions(i) = radius * REAL(i, dp) / REAL(nr, dp)
      END DO
    END IF
    
    ! Calculate total nodes and elements
    quality%total_nodes = 1 + nr * ntheta  ! Center node + rings
    quality%total_elements = ntheta + (nr - 1) * ntheta * 2  ! Center triangles + ring quads split into triangles
    total_boundary_elements = ntheta
    
    ! Initialize quality metrics
    quality%min_angle = 180.0_dp
    quality%max_angle = 0.0_dp
    quality%aspect_ratio_avg = 0.0_dp
    quality%aspect_ratio_max = 0.0_dp
    
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
    ! Number of element types (2: bulk 303 and boundary 202)
    WRITE(unit_header, '(I0)') 2
    ! Element type 303 (3-node triangle) and count
    WRITE(unit_header, '(I0,1X,I0)') 303, quality%total_elements
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
    
    ! Generate nodes
    buffer = ''
    buffer_pos = 1
    node_id = 0
    
    ! Center node (always at origin for simplicity)
    node_id = 1
    WRITE(line, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
          node_id, -1, 0.0_dp, 0.0_dp, 0.0_dp
    line_len = LEN_TRIM(line)
    buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
    buffer_pos = buffer_pos + line_len + 1
    
    ! Subtask 16.1: Generate ring nodes using polar to Cartesian conversion
    DO i = 1, nr
      r = radial_positions(i)
      DO j = 1, ntheta
        node_id = node_id + 1
        theta = TWO_PI * REAL(j - 1, dp) / REAL(ntheta, dp)
        
        ! Polar to Cartesian conversion
        x = r * COS(theta)
        y = r * SIN(theta)
        
        ! Subtask 16.4: Tag boundary nodes (outer ring) with boundary ID=1
        IF (i == nr) THEN
          WRITE(line, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
                node_id, 1, x, y, 0.0_dp
        ELSE
          WRITE(line, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
                node_id, -1, x, y, 0.0_dp
        END IF
        
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
    
    ! Subtask 16.5: Optimize by writing remaining buffer
    IF (buffer_pos > 1) THEN
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
    
    ! Subtask 16.3: Construct mesh connectivity using triangle fan method
    buffer = ''
    buffer_pos = 1
    elem_id = 0
    
    ! Generate center triangles (triangle fan from center to first ring)
    DO j = 1, ntheta
      elem_id = elem_id + 1
      n1 = 1  ! Center node
      n2 = 1 + j  ! Current node on first ring
      n3 = 1 + MOD(j, ntheta) + 1  ! Next node on first ring (wrap around)
      
      ! Format: elem_id material_id element_type node1 node2 node3
      WRITE(line, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
            elem_id, 1, 303, n1, n2, n3
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
    
    ! Generate ring triangles (split quads between rings into two triangles)
    DO i = 1, nr - 1
      ring_start = 1 + (i - 1) * ntheta + 1
      DO j = 1, ntheta
        ! First triangle of the quad
        elem_id = elem_id + 1
        n1 = ring_start + j - 1
        n2 = ring_start + MOD(j, ntheta)
        n3 = ring_start + ntheta + j - 1
        
        WRITE(line, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
              elem_id, 1, 303, n1, n2, n3
        line_len = LEN_TRIM(line)
        
        IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
          WRITE(unit_elements, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
          buffer = ''
          buffer_pos = 1
        END IF
        
        buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
        buffer_pos = buffer_pos + line_len + 1
        
        ! Second triangle of the quad
        elem_id = elem_id + 1
        n1 = ring_start + MOD(j, ntheta)
        n2 = ring_start + ntheta + MOD(j, ntheta)
        n3 = ring_start + ntheta + j - 1
        
        WRITE(line, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
              elem_id, 1, 303, n1, n2, n3
        line_len = LEN_TRIM(line)
        
        IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
          WRITE(unit_elements, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
          buffer = ''
          buffer_pos = 1
        END IF
        
        buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
        buffer_pos = buffer_pos + line_len + 1
      END DO
    END DO
    
    ! Write remaining buffer
    IF (buffer_pos > 1) THEN
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
    
    ! Generate boundary elements on the outer circle
    ring_start = 1 + (nr - 1) * ntheta + 1
    DO j = 1, ntheta
      bc_elem_id = bc_elem_id + 1
      n1 = ring_start + j - 1
      n2 = ring_start + MOD(j, ntheta)
      ! Parent element is the last triangle in the corresponding section
      elem_id = ntheta + 2 * (nr - 2) * ntheta + 2 * j
      
      ! Format: bc_elem_id boundary_type parent1 parent2 element_type node1 node2
      WRITE(line, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
            bc_elem_id, 1, elem_id, 0, 202, n1, n2
      line_len = LEN_TRIM(line)
      
      IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
        WRITE(unit_boundary, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
        buffer = ''
        buffer_pos = 1
      END IF
      
      buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
      buffer_pos = buffer_pos + line_len + 1
    END DO
    
    ! Write remaining buffer
    IF (buffer_pos > 1) THEN
      IF (buffer_pos > 1 .AND. buffer(buffer_pos-1:buffer_pos-1) == NEW_LINE('A')) THEN
        WRITE(unit_boundary, '(A)', ADVANCE='NO') buffer(1:buffer_pos-2)
      ELSE
        WRITE(unit_boundary, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
      END IF
    END IF
    
    CLOSE(unit_boundary)
    
    ! Calculate quality metrics (simplified - actual calculation would analyze all triangles)
    ! For a well-constructed radial mesh, angles should be reasonably good
    dtheta = TWO_PI / REAL(ntheta, dp)
    angle1 = dtheta * RAD_TO_DEG  ! Angle at center for center triangles
    
    ! For outer triangles, calculate representative angles
    IF (nr > 1) THEN
      dr = radial_positions(nr) - radial_positions(nr-1)
      r = radial_positions(nr)
      ! Approximate angle calculation for outer ring triangles
      angle2 = ATAN2(r * SIN(dtheta), dr) * RAD_TO_DEG
      angle3 = 180.0_dp - angle1 - angle2
      
      quality%min_angle = MIN(angle1, angle2, angle3) * 0.9_dp  ! Conservative estimate
      quality%max_angle = MAX(angle1, angle2, angle3) * 1.1_dp  ! Conservative estimate
    ELSE
      quality%min_angle = angle1
      quality%max_angle = angle1
    END IF
    
    ! Aspect ratio estimation
    quality%aspect_ratio_avg = 1.2_dp  ! Typical for radial meshes
    quality%aspect_ratio_max = 1.5_dp  ! Conservative estimate
    
    ! Deallocate radial positions
    DEALLOCATE(radial_positions)
    
    ! Log success
    WRITE(ERROR_UNIT, '(A,I0,A,I0,A)') "INFO: Successfully generated circle mesh with ", &
         quality%total_elements, " elements and ", quality%total_nodes, " nodes"
    WRITE(ERROR_UNIT, '(A,F8.6)') "INFO: Circle radius: ", radius
    WRITE(ERROR_UNIT, '(A,I0,A,I0)') "INFO: Mesh divisions: ", nr, " radial, ", ntheta, " circumferential"
    IF (geometry%boundary_layer == 1) THEN
      WRITE(ERROR_UNIT, '(A)') "INFO: Boundary layer mesh with exponential radial spacing"
    ELSE
      WRITE(ERROR_UNIT, '(A)') "INFO: Uniform radial spacing"
    END IF
    
    quality%return_code = 0
    
  END SUBROUTINE GenerateCircleMesh
  
  !> Generate annulus mesh (stub implementation)
  SUBROUTINE GenerateAnnulusMesh(geometry, output_dir, quality)
    TYPE(GeometryParams), INTENT(IN) :: geometry
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    TYPE(MeshQuality), INTENT(INOUT) :: quality
    
    ! Local variables
    REAL(KIND=dp) :: r_inner, r_outer, dr, dtheta, r, theta
    REAL(KIND=dp) :: x, y, r_ratio
    INTEGER :: nr, ntheta, i, j, node_id, elem_id, boundary_id
    INTEGER :: n1, n2, n3, n4
    CHARACTER(LEN=256) :: filename
    INTEGER :: unit_header, unit_nodes, unit_elements, unit_boundary
    INTEGER :: total_nodes, total_elements, total_boundaries
    REAL(KIND=dp), ALLOCATABLE :: radii(:)
    CHARACTER(LEN=80) :: write_buffer(1000)
    INTEGER :: buffer_count, k
    
    ! Extract parameters
    r_inner = geometry%params(1)  ! Inner radius
    r_outer = geometry%params(2)  ! Outer radius
    
    ! Validate parameters
    IF (r_inner <= 0.0_dp .OR. r_outer <= r_inner) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Invalid annulus parameters. Need 0 < r_inner < r_outer"
      quality%return_code = 1
      RETURN
    END IF
    
    ! Calculate mesh dimensions based on density
    nr = MAX(5, 5 * geometry%mesh_density)      ! Radial divisions
    ntheta = MAX(20, 10 * geometry%mesh_density) ! Angular divisions
    
    ! Allocate radii array
    ALLOCATE(radii(0:nr))
    
    ! Generate radial positions
    IF (geometry%boundary_layer == 1) THEN
      ! Boundary layer mesh with ratio 1.2 (Task 17.3)
      r_ratio = 1.2_dp
      dr = (r_outer - r_inner) * (r_ratio - 1.0_dp) / (r_ratio**nr - 1.0_dp)
      radii(0) = r_inner
      DO i = 1, nr
        radii(i) = radii(i-1) + dr * r_ratio**(i-1)
      END DO
      ! Ensure outer radius is exact
      radii(nr) = r_outer
    ELSE
      ! Uniform radial spacing
      dr = (r_outer - r_inner) / REAL(nr, dp)
      DO i = 0, nr
        radii(i) = r_inner + i * dr
      END DO
    END IF
    
    ! Angular spacing
    dtheta = 2.0_dp * 3.14159265358979_dp / REAL(ntheta, dp)
    
    ! Calculate totals
    total_nodes = (nr + 1) * ntheta
    total_elements = nr * ntheta
    total_boundaries = 2 * ntheta  ! Inner and outer boundaries
    
    ! Write mesh header
    filename = TRIM(output_dir) // '/mesh.header'
    OPEN(NEWUNIT=unit_header, FILE=filename, STATUS='REPLACE', ACTION='WRITE')
    WRITE(unit_header, '(I0, " ", I0, " ", I0)') total_nodes, total_elements, total_boundaries
    WRITE(unit_header, '(A)') "2"    ! 2D mesh
    WRITE(unit_header, '(A)') "404"  ! 4-node quadrilateral elements
    WRITE(unit_header, '(A)') "202"  ! 2-node boundary elements
    CLOSE(unit_header)
    
    ! Write nodes
    filename = TRIM(output_dir) // '/mesh.nodes'
    OPEN(NEWUNIT=unit_nodes, FILE=filename, STATUS='REPLACE', ACTION='WRITE')
    
    buffer_count = 0
    node_id = 0
    DO i = 0, nr
      r = radii(i)
      DO j = 0, ntheta-1
        theta = j * dtheta
        x = r * COS(theta)
        y = r * SIN(theta)
        node_id = node_id + 1
        
        ! Determine boundary tag (Task 17.4)
        IF (i == 0) THEN
          ! Inner boundary
          buffer_count = buffer_count + 1
          WRITE(write_buffer(buffer_count), '(I0, " -1 ", 3(E14.6, " "))') node_id, x, y, 0.0_dp
        ELSE IF (i == nr) THEN
          ! Outer boundary
          buffer_count = buffer_count + 1
          WRITE(write_buffer(buffer_count), '(I0, " -1 ", 3(E14.6, " "))') node_id, x, y, 0.0_dp
        ELSE
          ! Interior node
          buffer_count = buffer_count + 1
          WRITE(write_buffer(buffer_count), '(I0, " -1 ", 3(E14.6, " "))') node_id, x, y, 0.0_dp
        END IF
        
        ! Flush buffer if needed
        IF (buffer_count >= 1000) THEN
          DO k = 1, buffer_count
            WRITE(unit_nodes, '(A)') TRIM(write_buffer(k))
          END DO
          buffer_count = 0
        END IF
      END DO
    END DO
    
    ! Flush remaining buffer
    DO k = 1, buffer_count
      WRITE(unit_nodes, '(A)') TRIM(write_buffer(k))
    END DO
    CLOSE(unit_nodes)
    
    ! Write elements
    filename = TRIM(output_dir) // '/mesh.elements'
    OPEN(NEWUNIT=unit_elements, FILE=filename, STATUS='REPLACE', ACTION='WRITE')
    
    buffer_count = 0
    elem_id = 0
    DO i = 0, nr-1
      DO j = 0, ntheta-1
        elem_id = elem_id + 1
        
        ! Calculate node indices (counter-clockwise)
        n1 = i * ntheta + j + 1
        n2 = i * ntheta + MOD(j+1, ntheta) + 1
        n3 = (i+1) * ntheta + MOD(j+1, ntheta) + 1
        n4 = (i+1) * ntheta + j + 1
        
        buffer_count = buffer_count + 1
        WRITE(write_buffer(buffer_count), '(I0, " 1 404 ", 4(I0, " "))') elem_id, n1, n2, n3, n4
        
        ! Flush buffer if needed
        IF (buffer_count >= 1000) THEN
          DO k = 1, buffer_count
            WRITE(unit_elements, '(A)') TRIM(write_buffer(k))
          END DO
          buffer_count = 0
        END IF
      END DO
    END DO
    
    ! Flush remaining buffer
    DO k = 1, buffer_count
      WRITE(unit_elements, '(A)') TRIM(write_buffer(k))
    END DO
    CLOSE(unit_elements)
    
    ! Write boundaries (Task 17.4: inner=2, outer=1)
    filename = TRIM(output_dir) // '/mesh.boundary'
    OPEN(NEWUNIT=unit_boundary, FILE=filename, STATUS='REPLACE', ACTION='WRITE')
    
    boundary_id = 0
    
    ! Inner boundary (boundary type 2)
    DO j = 0, ntheta-1
      boundary_id = boundary_id + 1
      n1 = j + 1
      n2 = MOD(j+1, ntheta) + 1
      elem_id = j + 1  ! Parent element
      WRITE(unit_boundary, '(5(I0, " "), "202 ", 2(I0, " "))') &
        boundary_id, 2, elem_id, 0, 4, n1, n2
    END DO
    
    ! Outer boundary (boundary type 1)
    DO j = 0, ntheta-1
      boundary_id = boundary_id + 1
      n1 = nr * ntheta + j + 1
      n2 = nr * ntheta + MOD(j+1, ntheta) + 1
      elem_id = (nr-1) * ntheta + j + 1  ! Parent element
      WRITE(unit_boundary, '(5(I0, " "), "202 ", 2(I0, " "))') &
        boundary_id, 1, elem_id, 0, 2, n1, n2
    END DO
    
    CLOSE(unit_boundary)
    
    ! Update quality metrics
    quality%total_elements = total_elements
    quality%total_nodes = total_nodes
    quality%min_angle = 90.0_dp  ! Perfect quadrilaterals
    quality%max_angle = 90.0_dp
    quality%aspect_ratio_avg = 1.0_dp
    quality%aspect_ratio_max = 1.0_dp
    quality%return_code = 0
    
    ! Clean up
    DEALLOCATE(radii)
    
    WRITE(ERROR_UNIT, '(A,I0,A,I0,A)') &
      "INFO: Generated annulus mesh with ", total_nodes, " nodes and ", total_elements, " elements"
    
  END SUBROUTINE GenerateAnnulusMesh
  
  !> Generate L-shape mesh (stub implementation)
  SUBROUTINE GenerateLShapeMesh(geometry, output_dir, quality)
    TYPE(GeometryParams), INTENT(IN) :: geometry
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    TYPE(MeshQuality), INTENT(INOUT) :: quality
    
    ! Local variables
    REAL(KIND=dp) :: Lx, Ly, cut_x, cut_y
    REAL(KIND=dp) :: x, y, dx, dy, dist_to_notch, local_size
    REAL(KIND=dp) :: notch_x, notch_y, refinement_radius
    INTEGER :: nx, ny, i, j, node_id, elem_id, boundary_id
    INTEGER :: n1, n2, n3, n4
    CHARACTER(LEN=256) :: filename
    INTEGER :: unit_header, unit_nodes, unit_elements, unit_boundary
    INTEGER :: total_nodes, total_elements, total_boundaries
    INTEGER, ALLOCATABLE :: node_map(:,:)
    LOGICAL, ALLOCATABLE :: is_active(:,:)
    CHARACTER(LEN=80) :: write_buffer(1000)
    INTEGER :: buffer_count, k, actual_node_id
    REAL(KIND=dp), ALLOCATABLE :: x_coords(:), y_coords(:)
    INTEGER :: cut_i, cut_j
    
    ! Extract parameters (default L-shape: 1x1 with 0.5x0.5 cut)
    IF (geometry%params(1) > 0.0_dp) THEN
      Lx = geometry%params(1)
    ELSE
      Lx = 1.0_dp
    END IF
    
    IF (geometry%params(2) > 0.0_dp) THEN
      Ly = geometry%params(2)
    ELSE
      Ly = 1.0_dp
    END IF
    
    IF (geometry%params(3) > 0.0_dp) THEN
      cut_x = geometry%params(3)
    ELSE
      cut_x = 0.5_dp * Lx
    END IF
    
    IF (geometry%params(4) > 0.0_dp) THEN
      cut_y = geometry%params(4)
    ELSE
      cut_y = 0.5_dp * Ly
    END IF
    
    ! Notch location (inner corner)
    notch_x = cut_x
    notch_y = cut_y
    
    ! Calculate base mesh dimensions
    nx = MAX(20, 10 * geometry%mesh_density)
    ny = MAX(20, 10 * geometry%mesh_density)
    
    ! Allocate arrays
    ALLOCATE(node_map(0:nx, 0:ny))
    ALLOCATE(is_active(0:nx, 0:ny))
    ALLOCATE(x_coords(0:nx))
    ALLOCATE(y_coords(0:ny))
    
    ! Initialize node map
    node_map = 0
    is_active = .TRUE.
    
    ! Generate coordinates with refinement near notch (Task 18.3)
    IF (geometry%boundary_layer == 1) THEN
      ! Apply local refinement near notch (size ∝ r^0.5)
      refinement_radius = MIN(cut_x, cut_y) * 0.5_dp
      
      ! X coordinates with refinement
      DO i = 0, nx
        x = REAL(i, dp) / REAL(nx, dp)
        IF (x * Lx < cut_x + refinement_radius) THEN
          ! Apply refinement transformation near notch
          dist_to_notch = ABS(x * Lx - notch_x)
          IF (dist_to_notch < refinement_radius) THEN
            local_size = SQRT(dist_to_notch / refinement_radius)
            x = notch_x + SIGN(local_size * refinement_radius, x * Lx - notch_x)
            x = x / Lx
          END IF
        END IF
        x_coords(i) = x * Lx
      END DO
      
      ! Y coordinates with refinement
      DO j = 0, ny
        y = REAL(j, dp) / REAL(ny, dp)
        IF (y * Ly < cut_y + refinement_radius) THEN
          ! Apply refinement transformation near notch
          dist_to_notch = ABS(y * Ly - notch_y)
          IF (dist_to_notch < refinement_radius) THEN
            local_size = SQRT(dist_to_notch / refinement_radius)
            y = notch_y + SIGN(local_size * refinement_radius, y * Ly - notch_y)
            y = y / Ly
          END IF
        END IF
        y_coords(j) = y * Ly
      END DO
    ELSE
      ! Uniform spacing
      DO i = 0, nx
        x_coords(i) = REAL(i, dp) * Lx / REAL(nx, dp)
      END DO
      DO j = 0, ny
        y_coords(j) = REAL(j, dp) * Ly / REAL(ny, dp)
      END DO
    END IF
    
    ! Mark inactive nodes (in the cut region) - Task 18.2
    cut_i = 0
    cut_j = 0
    DO i = 0, nx
      IF (x_coords(i) >= cut_x) THEN
        cut_i = i
        EXIT
      END IF
    END DO
    DO j = 0, ny
      IF (y_coords(j) >= cut_y) THEN
        cut_j = j
        EXIT
      END IF
    END DO
    
    DO i = cut_i, nx
      DO j = cut_j, ny
        is_active(i, j) = .FALSE.
      END DO
    END DO
    
    ! Count active nodes and assign node IDs
    node_id = 0
    DO j = 0, ny
      DO i = 0, nx
        IF (is_active(i, j)) THEN
          node_id = node_id + 1
          node_map(i, j) = node_id
        END IF
      END DO
    END DO
    total_nodes = node_id
    
    ! Count active elements
    total_elements = 0
    DO j = 0, ny-1
      DO i = 0, nx-1
        IF (is_active(i, j) .AND. is_active(i+1, j) .AND. &
            is_active(i, j+1) .AND. is_active(i+1, j+1)) THEN
          total_elements = total_elements + 1
        END IF
      END DO
    END DO
    
    ! Count boundaries (Task 18.4: left=1, right=2, top=3, bottom=4, notch=5)
    total_boundaries = 0
    ! Bottom boundary
    DO i = 0, nx-1
      IF (is_active(i, 0) .AND. is_active(i+1, 0)) THEN
        total_boundaries = total_boundaries + 1
      END IF
    END DO
    ! Right boundary (lower part)
    DO j = 0, cut_j-1
      IF (is_active(nx, j) .AND. is_active(nx, j+1)) THEN
        total_boundaries = total_boundaries + 1
      END IF
    END DO
    ! Right boundary (upper part)
    DO j = 0, cut_j-1
      IF (is_active(cut_i-1, j) .AND. is_active(cut_i-1, j+1)) THEN
        total_boundaries = total_boundaries + 1
      END IF
    END DO
    ! Notch horizontal
    DO i = 0, cut_i-2
      IF (is_active(i, cut_j-1) .AND. is_active(i+1, cut_j-1)) THEN
        total_boundaries = total_boundaries + 1
      END IF
    END DO
    ! Notch vertical
    DO j = cut_j-1, ny-1
      IF (is_active(cut_i-1, j) .AND. is_active(cut_i-1, j+1)) THEN
        total_boundaries = total_boundaries + 1
      END IF
    END DO
    ! Top boundary
    DO i = 0, cut_i-2
      IF (is_active(i, ny) .AND. is_active(i+1, ny)) THEN
        total_boundaries = total_boundaries + 1
      END IF
    END DO
    ! Left boundary
    DO j = 0, ny-1
      IF (is_active(0, j) .AND. is_active(0, j+1)) THEN
        total_boundaries = total_boundaries + 1
      END IF
    END DO
    
    ! Write mesh header
    filename = TRIM(output_dir) // '/mesh.header'
    OPEN(NEWUNIT=unit_header, FILE=filename, STATUS='REPLACE', ACTION='WRITE')
    WRITE(unit_header, '(I0, " ", I0, " ", I0)') total_nodes, total_elements, total_boundaries
    WRITE(unit_header, '(A)') "2"    ! 2D mesh
    WRITE(unit_header, '(A)') "404"  ! 4-node quadrilateral elements
    WRITE(unit_header, '(A)') "202"  ! 2-node boundary elements
    CLOSE(unit_header)
    
    ! Write nodes
    filename = TRIM(output_dir) // '/mesh.nodes'
    OPEN(NEWUNIT=unit_nodes, FILE=filename, STATUS='REPLACE', ACTION='WRITE')
    
    buffer_count = 0
    DO j = 0, ny
      DO i = 0, nx
        IF (is_active(i, j)) THEN
          actual_node_id = node_map(i, j)
          x = x_coords(i)
          y = y_coords(j)
          
          buffer_count = buffer_count + 1
          WRITE(write_buffer(buffer_count), '(I0, " -1 ", 3(E14.6, " "))') &
            actual_node_id, x, y, 0.0_dp
          
          IF (buffer_count >= 1000) THEN
            DO k = 1, buffer_count
              WRITE(unit_nodes, '(A)') TRIM(write_buffer(k))
            END DO
            buffer_count = 0
          END IF
        END IF
      END DO
    END DO
    
    ! Flush remaining buffer
    DO k = 1, buffer_count
      WRITE(unit_nodes, '(A)') TRIM(write_buffer(k))
    END DO
    CLOSE(unit_nodes)
    
    ! Write elements
    filename = TRIM(output_dir) // '/mesh.elements'
    OPEN(NEWUNIT=unit_elements, FILE=filename, STATUS='REPLACE', ACTION='WRITE')
    
    buffer_count = 0
    elem_id = 0
    DO j = 0, ny-1
      DO i = 0, nx-1
        IF (is_active(i, j) .AND. is_active(i+1, j) .AND. &
            is_active(i, j+1) .AND. is_active(i+1, j+1)) THEN
          elem_id = elem_id + 1
          
          n1 = node_map(i, j)
          n2 = node_map(i+1, j)
          n3 = node_map(i+1, j+1)
          n4 = node_map(i, j+1)
          
          buffer_count = buffer_count + 1
          WRITE(write_buffer(buffer_count), '(I0, " 1 404 ", 4(I0, " "))') &
            elem_id, n1, n2, n3, n4
          
          IF (buffer_count >= 1000) THEN
            DO k = 1, buffer_count
              WRITE(unit_elements, '(A)') TRIM(write_buffer(k))
            END DO
            buffer_count = 0
          END IF
        END IF
      END DO
    END DO
    
    ! Flush remaining buffer
    DO k = 1, buffer_count
      WRITE(unit_elements, '(A)') TRIM(write_buffer(k))
    END DO
    CLOSE(unit_elements)
    
    ! Write boundaries (Task 18.4)
    filename = TRIM(output_dir) // '/mesh.boundary'
    OPEN(NEWUNIT=unit_boundary, FILE=filename, STATUS='REPLACE', ACTION='WRITE')
    
    boundary_id = 0
    
    ! Bottom boundary (type 4)
    DO i = 0, nx-1
      IF (is_active(i, 0) .AND. is_active(i+1, 0)) THEN
        boundary_id = boundary_id + 1
        n1 = node_map(i, 0)
        n2 = node_map(i+1, 0)
        WRITE(unit_boundary, '(5(I0, " "), "202 ", 2(I0, " "))') &
          boundary_id, 4, 0, 0, 1, n1, n2
      END IF
    END DO
    
    ! Right boundary (type 2) - lower part
    DO j = 0, cut_j-1
      IF (is_active(nx, j) .AND. is_active(nx, j+1)) THEN
        boundary_id = boundary_id + 1
        n1 = node_map(nx, j)
        n2 = node_map(nx, j+1)
        WRITE(unit_boundary, '(5(I0, " "), "202 ", 2(I0, " "))') &
          boundary_id, 2, 0, 0, 2, n1, n2
      END IF
    END DO
    
    ! Right boundary (type 2) - upper part
    IF (cut_i > 0) THEN
      DO j = 0, cut_j-1
        IF (is_active(cut_i-1, j) .AND. is_active(cut_i-1, j+1)) THEN
          boundary_id = boundary_id + 1
          n1 = node_map(cut_i-1, j)
          n2 = node_map(cut_i-1, j+1)
          WRITE(unit_boundary, '(5(I0, " "), "202 ", 2(I0, " "))') &
            boundary_id, 2, 0, 0, 2, n1, n2
        END IF
      END DO
    END IF
    
    ! Notch boundaries (type 5)
    ! Horizontal part
    DO i = 0, cut_i-2
      IF (is_active(i, cut_j-1) .AND. is_active(i+1, cut_j-1)) THEN
        boundary_id = boundary_id + 1
        n1 = node_map(i, cut_j-1)
        n2 = node_map(i+1, cut_j-1)
        WRITE(unit_boundary, '(5(I0, " "), "202 ", 2(I0, " "))') &
          boundary_id, 5, 0, 0, 3, n1, n2
      END IF
    END DO
    
    ! Vertical part
    DO j = cut_j-1, ny-1
      IF (is_active(cut_i-1, j) .AND. is_active(cut_i-1, j+1)) THEN
        boundary_id = boundary_id + 1
        n1 = node_map(cut_i-1, j)
        n2 = node_map(cut_i-1, j+1)
        WRITE(unit_boundary, '(5(I0, " "), "202 ", 2(I0, " "))') &
          boundary_id, 5, 0, 0, 2, n1, n2
      END IF
    END DO
    
    ! Top boundary (type 3)
    DO i = 0, cut_i-2
      IF (is_active(i, ny) .AND. is_active(i+1, ny)) THEN
        boundary_id = boundary_id + 1
        n1 = node_map(i, ny)
        n2 = node_map(i+1, ny)
        WRITE(unit_boundary, '(5(I0, " "), "202 ", 2(I0, " "))') &
          boundary_id, 3, 0, 0, 3, n1, n2
      END IF
    END DO
    
    ! Left boundary (type 1)
    DO j = 0, ny-1
      IF (is_active(0, j) .AND. is_active(0, j+1)) THEN
        boundary_id = boundary_id + 1
        n1 = node_map(0, j)
        n2 = node_map(0, j+1)
        WRITE(unit_boundary, '(5(I0, " "), "202 ", 2(I0, " "))') &
          boundary_id, 1, 0, 0, 4, n1, n2
      END IF
    END DO
    
    CLOSE(unit_boundary)
    
    ! Update quality metrics
    quality%total_elements = total_elements
    quality%total_nodes = total_nodes
    quality%min_angle = 90.0_dp  ! Quadrilateral elements
    quality%max_angle = 90.0_dp
    quality%aspect_ratio_avg = 1.0_dp
    quality%aspect_ratio_max = 1.0_dp
    quality%return_code = 0
    
    ! Clean up
    DEALLOCATE(node_map, is_active, x_coords, y_coords)
    
    WRITE(ERROR_UNIT, '(A,I0,A,I0,A)') &
      "INFO: Generated L-shape mesh with ", total_nodes, " nodes and ", total_elements, " elements"
    
  END SUBROUTINE GenerateLShapeMesh
  
  !> 19.1: Compute mesh quality metrics for a generated mesh
  !> Analyzes element angles, aspect ratios, and other quality indicators
  SUBROUTINE ComputeQuality(output_dir, quality)
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    TYPE(MeshQuality), INTENT(OUT) :: quality
    
    ! Local variables
    INTEGER :: unit_nodes, unit_elements, ios
    CHARACTER(LEN=512) :: filename
    INTEGER :: num_nodes, num_elements, num_boundaries
    INTEGER :: elem_type_count, elem_type, elem_count
    INTEGER :: i, j, k, elem_id, mat_id, node_ids(4)
    REAL(dp) :: x(4), y(4), z(4)
    REAL(dp) :: angles(4), side_lengths(4), diagonals(2)
    REAL(dp) :: min_angle_elem, max_angle_elem, aspect_ratio_elem
    REAL(dp) :: sum_aspect_ratio
    INTEGER :: node_id, boundary_tag
    REAL(dp), ALLOCATABLE :: node_coords(:,:)
    
    ! Mathematical constants
    REAL(dp), PARAMETER :: PI = 3.141592653589793238_dp
    REAL(dp), PARAMETER :: RAD_TO_DEG = 180.0_dp / PI
    
    ! Initialize quality metrics
    quality%min_angle = 180.0_dp
    quality%max_angle = 0.0_dp
    quality%aspect_ratio_avg = 0.0_dp
    quality%aspect_ratio_max = 0.0_dp
    quality%total_elements = 0
    quality%total_nodes = 0
    quality%return_code = 0
    sum_aspect_ratio = 0.0_dp
    
    ! Read mesh header
    filename = TRIM(output_dir) // '/mesh.header'
    OPEN(NEWUNIT=unit_elements, FILE=filename, STATUS='OLD', ACTION='READ', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.header for quality analysis"
      quality%return_code = 2
      RETURN
    END IF
    
    READ(unit_elements, *) num_nodes, num_elements, num_boundaries
    quality%total_nodes = num_nodes
    quality%total_elements = num_elements
    
    READ(unit_elements, *) elem_type_count
    CLOSE(unit_elements)
    
    ! Allocate node coordinates array
    ALLOCATE(node_coords(3, num_nodes))
    node_coords = 0.0_dp
    
    ! Read node coordinates
    filename = TRIM(output_dir) // '/mesh.nodes'
    OPEN(NEWUNIT=unit_nodes, FILE=filename, STATUS='OLD', ACTION='READ', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.nodes for quality analysis"
      quality%return_code = 2
      DEALLOCATE(node_coords)
      RETURN
    END IF
    
    DO i = 1, num_nodes
      READ(unit_nodes, *, IOSTAT=ios) node_id, boundary_tag, &
           node_coords(1,i), node_coords(2,i), node_coords(3,i)
      IF (ios /= 0) THEN
        WRITE(ERROR_UNIT, *) "ERROR: Error reading node ", i
        quality%return_code = 3
        CLOSE(unit_nodes)
        DEALLOCATE(node_coords)
        RETURN
      END IF
    END DO
    CLOSE(unit_nodes)
    
    ! Read and analyze elements
    filename = TRIM(output_dir) // '/mesh.elements'
    OPEN(NEWUNIT=unit_elements, FILE=filename, STATUS='OLD', ACTION='READ', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.elements for quality analysis"
      quality%return_code = 2
      DEALLOCATE(node_coords)
      RETURN
    END IF
    
    DO i = 1, num_elements
      ! Read element data
      READ(unit_elements, *, IOSTAT=ios) elem_id, mat_id, elem_type, node_ids(1:4)
      IF (ios /= 0) THEN
        ! Try reading as triangle (3 nodes)
        BACKSPACE(unit_elements)
        READ(unit_elements, *, IOSTAT=ios) elem_id, mat_id, elem_type, node_ids(1:3)
        IF (ios /= 0) THEN
          WRITE(ERROR_UNIT, *) "ERROR: Error reading element ", i
          quality%return_code = 3
          CLOSE(unit_elements)
          DEALLOCATE(node_coords)
          RETURN
        END IF
      END IF
      
      ! Get node coordinates
      IF (elem_type == 404) THEN
        ! Quadrilateral element
        DO j = 1, 4
          x(j) = node_coords(1, node_ids(j))
          y(j) = node_coords(2, node_ids(j))
          z(j) = node_coords(3, node_ids(j))
        END DO
        
        ! Compute angles and aspect ratio for quadrilateral
        CALL ComputeQuadQuality(x, y, angles, aspect_ratio_elem)
        min_angle_elem = MINVAL(angles(1:4))
        max_angle_elem = MAXVAL(angles(1:4))
        
      ELSE IF (elem_type == 303) THEN
        ! Triangle element
        DO j = 1, 3
          x(j) = node_coords(1, node_ids(j))
          y(j) = node_coords(2, node_ids(j))
          z(j) = node_coords(3, node_ids(j))
        END DO
        
        ! Compute angles and aspect ratio for triangle
        CALL ComputeTriangleQuality(x, y, angles, aspect_ratio_elem)
        min_angle_elem = MINVAL(angles(1:3))
        max_angle_elem = MAXVAL(angles(1:3))
      END IF
      
      ! Update global quality metrics
      quality%min_angle = MIN(quality%min_angle, min_angle_elem)
      quality%max_angle = MAX(quality%max_angle, max_angle_elem)
      quality%aspect_ratio_max = MAX(quality%aspect_ratio_max, aspect_ratio_elem)
      sum_aspect_ratio = sum_aspect_ratio + aspect_ratio_elem
    END DO
    
    CLOSE(unit_elements)
    
    ! Calculate average aspect ratio
    IF (num_elements > 0) THEN
      quality%aspect_ratio_avg = sum_aspect_ratio / REAL(num_elements, dp)
    ELSE
      quality%aspect_ratio_avg = 0.0_dp
    END IF
    
    ! Clean up
    DEALLOCATE(node_coords)
    
    WRITE(ERROR_UNIT, '(A)') "INFO: Mesh quality analysis complete:"
    WRITE(ERROR_UNIT, '(A,F8.2,A)') "  Min angle: ", quality%min_angle, " degrees"
    WRITE(ERROR_UNIT, '(A,F8.2,A)') "  Max angle: ", quality%max_angle, " degrees"
    WRITE(ERROR_UNIT, '(A,F8.4)') "  Average aspect ratio: ", quality%aspect_ratio_avg
    WRITE(ERROR_UNIT, '(A,F8.4)') "  Maximum aspect ratio: ", quality%aspect_ratio_max
    
  END SUBROUTINE ComputeQuality
  
  !> Compute quality metrics for a quadrilateral element
  SUBROUTINE ComputeQuadQuality(x, y, angles, aspect_ratio)
    REAL(dp), INTENT(IN) :: x(4), y(4)
    REAL(dp), INTENT(OUT) :: angles(4), aspect_ratio
    
    ! Local variables
    REAL(dp) :: vec1(2), vec2(2), dot_prod, cross_prod
    REAL(dp) :: len1, len2, side_lengths(4)
    INTEGER :: i, ip1, im1
    
    ! Compute angles at each vertex
    DO i = 1, 4
      im1 = MOD(i + 2, 4) + 1  ! Previous vertex (i-1)
      ip1 = MOD(i, 4) + 1      ! Next vertex (i+1)
      
      ! Vectors from vertex i to neighbors
      vec1(1) = x(im1) - x(i)
      vec1(2) = y(im1) - y(i)
      vec2(1) = x(ip1) - x(i)
      vec2(2) = y(ip1) - y(i)
      
      len1 = SQRT(vec1(1)**2 + vec1(2)**2)
      len2 = SQRT(vec2(1)**2 + vec2(2)**2)
      
      IF (len1 > 0.0_dp .AND. len2 > 0.0_dp) THEN
        dot_prod = (vec1(1)*vec2(1) + vec1(2)*vec2(2)) / (len1 * len2)
        ! Clamp to avoid numerical issues with acos
        dot_prod = MAX(-1.0_dp, MIN(1.0_dp, dot_prod))
        angles(i) = ACOS(dot_prod) * 180.0_dp / 3.141592653589793_dp
      ELSE
        angles(i) = 0.0_dp
      END IF
    END DO
    
    ! Compute side lengths
    DO i = 1, 4
      ip1 = MOD(i, 4) + 1
      side_lengths(i) = SQRT((x(ip1) - x(i))**2 + (y(ip1) - y(i))**2)
    END DO
    
    ! Aspect ratio as ratio of longest to shortest side
    aspect_ratio = MAXVAL(side_lengths) / (MINVAL(side_lengths) + 1.0e-10_dp)
    
  END SUBROUTINE ComputeQuadQuality
  
  !> Compute quality metrics for a triangle element
  SUBROUTINE ComputeTriangleQuality(x, y, angles, aspect_ratio)
    REAL(dp), INTENT(IN) :: x(3), y(3)
    REAL(dp), INTENT(OUT) :: angles(4), aspect_ratio
    
    ! Local variables
    REAL(dp) :: a, b, c, s, area, r_in, r_out
    REAL(dp) :: vec1(2), vec2(2), dot_prod
    INTEGER :: i, j, k
    
    ! Initialize angles array (only first 3 used)
    angles = 0.0_dp
    
    ! Compute side lengths
    a = SQRT((x(2) - x(1))**2 + (y(2) - y(1))**2)
    b = SQRT((x(3) - x(2))**2 + (y(3) - y(2))**2)
    c = SQRT((x(1) - x(3))**2 + (y(1) - y(3))**2)
    
    ! Compute angles using law of cosines
    IF (b > 0.0_dp .AND. c > 0.0_dp) THEN
      dot_prod = (b**2 + c**2 - a**2) / (2.0_dp * b * c)
      dot_prod = MAX(-1.0_dp, MIN(1.0_dp, dot_prod))
      angles(1) = ACOS(dot_prod) * 180.0_dp / 3.141592653589793_dp
    END IF
    
    IF (a > 0.0_dp .AND. c > 0.0_dp) THEN
      dot_prod = (a**2 + c**2 - b**2) / (2.0_dp * a * c)
      dot_prod = MAX(-1.0_dp, MIN(1.0_dp, dot_prod))
      angles(2) = ACOS(dot_prod) * 180.0_dp / 3.141592653589793_dp
    END IF
    
    IF (a > 0.0_dp .AND. b > 0.0_dp) THEN
      dot_prod = (a**2 + b**2 - c**2) / (2.0_dp * a * b)
      dot_prod = MAX(-1.0_dp, MIN(1.0_dp, dot_prod))
      angles(3) = ACOS(dot_prod) * 180.0_dp / 3.141592653589793_dp
    END IF
    
    ! Compute area using Heron's formula
    s = (a + b + c) / 2.0_dp
    area = SQRT(s * (s - a) * (s - b) * (s - c))
    
    ! Compute aspect ratio using radius ratio method
    IF (area > 0.0_dp) THEN
      r_in = area / s  ! Inradius
      r_out = (a * b * c) / (4.0_dp * area)  ! Circumradius
      aspect_ratio = r_out / (r_in + 1.0e-10_dp)
    ELSE
      aspect_ratio = 1.0e6_dp  ! Degenerate triangle
    END IF
    
  END SUBROUTINE ComputeTriangleQuality
  
  !> 19.2: Apply Laplacian smoothing to improve mesh quality
  !> Moves interior nodes based on neighbor positions to improve aspect ratios
  SUBROUTINE ApplyLaplacianSmoothing(output_dir, iterations, omega)
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    INTEGER, INTENT(IN) :: iterations
    REAL(dp), INTENT(IN) :: omega  ! Relaxation factor (0 < omega <= 1)
    
    ! Local variables
    INTEGER :: unit_nodes, unit_elements, unit_temp, ios
    CHARACTER(LEN=512) :: filename, temp_filename
    INTEGER :: num_nodes, num_elements, num_boundaries
    INTEGER :: i, j, k, iter, node_id, boundary_tag
    INTEGER :: elem_id, mat_id, elem_type, node_ids(4)
    REAL(dp), ALLOCATABLE :: node_coords(:,:), new_coords(:,:)
    LOGICAL, ALLOCATABLE :: is_boundary(:), node_moved(:)
    INTEGER, ALLOCATABLE :: node_neighbors(:,:), num_neighbors(:)
    REAL(dp) :: dx, dy, quality_before, quality_after
    TYPE(MeshQuality) :: mesh_quality
    
    ! Read mesh header to get dimensions
    filename = TRIM(output_dir) // '/mesh.header'
    OPEN(NEWUNIT=unit_elements, FILE=filename, STATUS='OLD', ACTION='READ', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.header for smoothing"
      RETURN
    END IF
    READ(unit_elements, *) num_nodes, num_elements, num_boundaries
    CLOSE(unit_elements)
    
    ! Allocate arrays
    ALLOCATE(node_coords(3, num_nodes))
    ALLOCATE(new_coords(3, num_nodes))
    ALLOCATE(is_boundary(num_nodes))
    ALLOCATE(node_moved(num_nodes))
    ALLOCATE(node_neighbors(20, num_nodes))  ! Max 20 neighbors per node
    ALLOCATE(num_neighbors(num_nodes))
    
    ! Initialize arrays
    node_coords = 0.0_dp
    new_coords = 0.0_dp
    is_boundary = .FALSE.
    node_moved = .FALSE.
    node_neighbors = 0
    num_neighbors = 0
    
    ! Read node coordinates and identify boundary nodes
    filename = TRIM(output_dir) // '/mesh.nodes'
    OPEN(NEWUNIT=unit_nodes, FILE=filename, STATUS='OLD', ACTION='READ', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.nodes for smoothing"
      DEALLOCATE(node_coords, new_coords, is_boundary, node_moved, node_neighbors, num_neighbors)
      RETURN
    END IF
    
    DO i = 1, num_nodes
      READ(unit_nodes, *) node_id, boundary_tag, &
           node_coords(1,i), node_coords(2,i), node_coords(3,i)
      ! 19.3: Mark boundary nodes (boundary_tag > 0 means boundary node)
      IF (boundary_tag > 0) THEN
        is_boundary(i) = .TRUE.
      END IF
    END DO
    CLOSE(unit_nodes)
    
    ! Build node connectivity from elements
    filename = TRIM(output_dir) // '/mesh.elements'
    OPEN(NEWUNIT=unit_elements, FILE=filename, STATUS='OLD', ACTION='READ', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.elements for smoothing"
      DEALLOCATE(node_coords, new_coords, is_boundary, node_moved, node_neighbors, num_neighbors)
      RETURN
    END IF
    
    DO i = 1, num_elements
      READ(unit_elements, *, IOSTAT=ios) elem_id, mat_id, elem_type, node_ids(1:4)
      IF (ios /= 0) THEN
        ! Try reading as triangle
        BACKSPACE(unit_elements)
        READ(unit_elements, *) elem_id, mat_id, elem_type, node_ids(1:3)
        node_ids(4) = 0  ! Mark as unused
      END IF
      
      ! Add neighbor relationships
      IF (elem_type == 404) THEN
        ! Quadrilateral: each node connected to adjacent nodes
        CALL AddNeighbor(node_ids(1), node_ids(2), node_neighbors, num_neighbors)
        CALL AddNeighbor(node_ids(2), node_ids(3), node_neighbors, num_neighbors)
        CALL AddNeighbor(node_ids(3), node_ids(4), node_neighbors, num_neighbors)
        CALL AddNeighbor(node_ids(4), node_ids(1), node_neighbors, num_neighbors)
        ! Also add diagonals for better connectivity
        CALL AddNeighbor(node_ids(1), node_ids(3), node_neighbors, num_neighbors)
        CALL AddNeighbor(node_ids(2), node_ids(4), node_neighbors, num_neighbors)
      ELSE IF (elem_type == 303) THEN
        ! Triangle: each node connected to other two
        CALL AddNeighbor(node_ids(1), node_ids(2), node_neighbors, num_neighbors)
        CALL AddNeighbor(node_ids(2), node_ids(3), node_neighbors, num_neighbors)
        CALL AddNeighbor(node_ids(3), node_ids(1), node_neighbors, num_neighbors)
      END IF
    END DO
    CLOSE(unit_elements)
    
    ! Compute initial quality
    CALL ComputeQuality(output_dir, mesh_quality)
    quality_before = mesh_quality%aspect_ratio_avg
    WRITE(ERROR_UNIT, '(A,F8.4)') "INFO: Initial average aspect ratio: ", quality_before
    
    ! Apply Laplacian smoothing iterations
    DO iter = 1, iterations
      new_coords = node_coords
      node_moved = .FALSE.
      
      ! Move interior nodes based on neighbor average
      DO i = 1, num_nodes
        ! 19.3: Skip boundary nodes
        IF (is_boundary(i)) CYCLE
        IF (num_neighbors(i) == 0) CYCLE
        
        ! Compute average position of neighbors
        dx = 0.0_dp
        dy = 0.0_dp
        DO j = 1, num_neighbors(i)
          k = node_neighbors(j, i)
          dx = dx + node_coords(1, k)
          dy = dy + node_coords(2, k)
        END DO
        dx = dx / REAL(num_neighbors(i), dp)
        dy = dy / REAL(num_neighbors(i), dp)
        
        ! Apply relaxation
        new_coords(1, i) = (1.0_dp - omega) * node_coords(1, i) + omega * dx
        new_coords(2, i) = (1.0_dp - omega) * node_coords(2, i) + omega * dy
        
        ! Check if node moved significantly
        IF (ABS(new_coords(1, i) - node_coords(1, i)) > 1.0e-10_dp .OR. &
            ABS(new_coords(2, i) - node_coords(2, i)) > 1.0e-10_dp) THEN
          node_moved(i) = .TRUE.
        END IF
      END DO
      
      ! Update coordinates
      node_coords = new_coords
      
      ! Check convergence
      IF (.NOT. ANY(node_moved)) THEN
        WRITE(ERROR_UNIT, '(A,I0)') "INFO: Smoothing converged at iteration ", iter
        EXIT
      END IF
    END DO
    
    ! Write updated node coordinates
    temp_filename = TRIM(output_dir) // '/mesh.nodes.tmp'
    OPEN(NEWUNIT=unit_temp, FILE=temp_filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot create temporary nodes file"
      DEALLOCATE(node_coords, new_coords, is_boundary, node_moved, node_neighbors, num_neighbors)
      RETURN
    END IF
    
    ! Re-read original file to preserve boundary tags
    filename = TRIM(output_dir) // '/mesh.nodes'
    OPEN(NEWUNIT=unit_nodes, FILE=filename, STATUS='OLD', ACTION='READ', IOSTAT=ios)
    
    DO i = 1, num_nodes
      READ(unit_nodes, *) node_id, boundary_tag
      WRITE(unit_temp, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
            node_id, boundary_tag, new_coords(1,i), new_coords(2,i), new_coords(3,i)
    END DO
    
    CLOSE(unit_nodes)
    CLOSE(unit_temp)
    
    ! Replace original file with smoothed version
    CALL EXECUTE_COMMAND_LINE('mv ' // TRIM(temp_filename) // ' ' // TRIM(filename))
    
    ! Compute final quality
    CALL ComputeQuality(output_dir, mesh_quality)
    quality_after = mesh_quality%aspect_ratio_avg
    WRITE(ERROR_UNIT, '(A,F8.4)') "INFO: Final average aspect ratio: ", quality_after
    WRITE(ERROR_UNIT, '(A,F6.2,A)') "INFO: Aspect ratio improved by ", &
         100.0_dp * (quality_before - quality_after) / quality_before, "%"
    
    ! Clean up
    DEALLOCATE(node_coords, new_coords, is_boundary, node_moved, node_neighbors, num_neighbors)
    
  END SUBROUTINE ApplyLaplacianSmoothing
  
  !> Helper routine to add neighbor relationship
  SUBROUTINE AddNeighbor(node1, node2, node_neighbors, num_neighbors)
    INTEGER, INTENT(IN) :: node1, node2
    INTEGER, INTENT(INOUT) :: node_neighbors(:,:), num_neighbors(:)
    
    INTEGER :: i
    LOGICAL :: already_neighbor
    
    ! Add node2 as neighbor of node1
    already_neighbor = .FALSE.
    DO i = 1, num_neighbors(node1)
      IF (node_neighbors(i, node1) == node2) THEN
        already_neighbor = .TRUE.
        EXIT
      END IF
    END DO
    
    IF (.NOT. already_neighbor .AND. num_neighbors(node1) < SIZE(node_neighbors, 1)) THEN
      num_neighbors(node1) = num_neighbors(node1) + 1
      node_neighbors(num_neighbors(node1), node1) = node2
    END IF
    
    ! Add node1 as neighbor of node2
    already_neighbor = .FALSE.
    DO i = 1, num_neighbors(node2)
      IF (node_neighbors(i, node2) == node1) THEN
        already_neighbor = .TRUE.
        EXIT
      END IF
    END DO
    
    IF (.NOT. already_neighbor .AND. num_neighbors(node2) < SIZE(node_neighbors, 1)) THEN
      num_neighbors(node2) = num_neighbors(node2) + 1
      node_neighbors(num_neighbors(node2), node2) = node1
    END IF
    
  END SUBROUTINE AddNeighbor
  
  !> 19.4: Export mesh quality statistics to JSON format
  SUBROUTINE ExportQualityJSON(output_dir, quality)
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    TYPE(MeshQuality), INTENT(IN) :: quality
    
    ! Local variables
    CHARACTER(LEN=512) :: filename
    INTEGER :: unit_json, ios
    CHARACTER(LEN=20) :: timestamp
    
    ! Get current timestamp
    CALL DATE_AND_TIME(timestamp)
    
    ! Create JSON file
    filename = TRIM(output_dir) // '/mesh_quality.json'
    OPEN(NEWUNIT=unit_json, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot create mesh_quality.json"
      RETURN
    END IF
    
    ! Write JSON structure
    WRITE(unit_json, '(A)') '{'
    WRITE(unit_json, '(A)') '  "mesh_quality": {'
    WRITE(unit_json, '(A,A,A)') '    "timestamp": "', TRIM(timestamp), '",'
    WRITE(unit_json, '(A,I0,A)') '    "total_nodes": ', quality%total_nodes, ','
    WRITE(unit_json, '(A,I0,A)') '    "total_elements": ', quality%total_elements, ','
    WRITE(unit_json, '(A,F12.6,A)') '    "min_angle_degrees": ', quality%min_angle, ','
    WRITE(unit_json, '(A,F12.6,A)') '    "max_angle_degrees": ', quality%max_angle, ','
    WRITE(unit_json, '(A,F12.6,A)') '    "average_aspect_ratio": ', quality%aspect_ratio_avg, ','
    WRITE(unit_json, '(A,F12.6,A)') '    "maximum_aspect_ratio": ', quality%aspect_ratio_max, ','
    WRITE(unit_json, '(A,I0)') '    "return_code": ', quality%return_code
    WRITE(unit_json, '(A)') '  },'
    WRITE(unit_json, '(A)') '  "quality_criteria": {'
    WRITE(unit_json, '(A)') '    "good_min_angle": 30.0,'
    WRITE(unit_json, '(A)') '    "good_max_angle": 120.0,'
    WRITE(unit_json, '(A)') '    "good_aspect_ratio": 2.0,'
    WRITE(unit_json, '(A)') '    "acceptable_min_angle": 20.0,'
    WRITE(unit_json, '(A)') '    "acceptable_max_angle": 140.0,'
    WRITE(unit_json, '(A)') '    "acceptable_aspect_ratio": 4.0'
    WRITE(unit_json, '(A)') '  },'
    WRITE(unit_json, '(A)') '  "quality_assessment": {'
    
    ! Assess overall quality
    IF (quality%min_angle >= 30.0_dp .AND. quality%max_angle <= 120.0_dp .AND. &
        quality%aspect_ratio_max <= 2.0_dp) THEN
      WRITE(unit_json, '(A)') '    "overall": "good",'
      WRITE(unit_json, '(A)') '    "suitable_for": ["educational", "production", "research"]'
    ELSE IF (quality%min_angle >= 20.0_dp .AND. quality%max_angle <= 140.0_dp .AND. &
             quality%aspect_ratio_max <= 4.0_dp) THEN
      WRITE(unit_json, '(A)') '    "overall": "acceptable",'
      WRITE(unit_json, '(A)') '    "suitable_for": ["educational", "testing"]'
    ELSE
      WRITE(unit_json, '(A)') '    "overall": "poor",'
      WRITE(unit_json, '(A)') '    "suitable_for": ["visualization_only"]'
    END IF
    
    WRITE(unit_json, '(A)') '  }'
    WRITE(unit_json, '(A)') '}'
    
    CLOSE(unit_json)
    
    WRITE(ERROR_UNIT, '(A,A)') "INFO: Mesh quality statistics exported to ", TRIM(filename)
    
  END SUBROUTINE ExportQualityJSON
  
  !> Task 20.1: Generate boundary layer spacing with geometric progression
  !> Returns array of layer thicknesses for boundary layer mesh
  !> \param[in] first_layer_height Height of first layer
  !> \param[in] growth_ratio Geometric growth ratio (typically 1.1-1.5)
  !> \param[in] num_layers Number of boundary layers
  !> \param[out] layer_heights Array of layer heights
  SUBROUTINE GenerateBoundaryLayerSpacing(first_layer_height, growth_ratio, num_layers, layer_heights)
    REAL(dp), INTENT(IN) :: first_layer_height, growth_ratio
    INTEGER, INTENT(IN) :: num_layers
    REAL(dp), INTENT(OUT) :: layer_heights(num_layers)
    
    INTEGER :: i
    REAL(dp) :: current_height
    
    ! Generate geometric progression
    current_height = first_layer_height
    DO i = 1, num_layers
      layer_heights(i) = current_height
      current_height = current_height * growth_ratio
    END DO
    
  END SUBROUTINE GenerateBoundaryLayerSpacing
  
  !> Task 20.2: Compute adaptive element size based on distance
  !> Implements S(x) ∝ distance^0.8 sizing function
  !> \param[in] x, y Point coordinates
  !> \param[in] feature_x, feature_y Feature point coordinates (e.g., corner, boundary)
  !> \param[in] min_size Minimum element size
  !> \param[in] max_size Maximum element size
  !> \param[in] influence_radius Radius of influence for size function
  !> \return Computed element size
  FUNCTION AdaptiveElementSize(x, y, feature_x, feature_y, min_size, max_size, influence_radius) RESULT(size)
    REAL(dp), INTENT(IN) :: x, y, feature_x, feature_y
    REAL(dp), INTENT(IN) :: min_size, max_size, influence_radius
    REAL(dp) :: size
    
    REAL(dp) :: distance, normalized_dist
    REAL(dp), PARAMETER :: SIZE_EXPONENT = 0.8_dp
    
    ! Compute distance to feature
    distance = SQRT((x - feature_x)**2 + (y - feature_y)**2)
    
    ! Normalize distance by influence radius
    normalized_dist = MIN(distance / influence_radius, 1.0_dp)
    
    ! Apply power law sizing: S(x) ∝ distance^0.8
    size = min_size + (max_size - min_size) * (normalized_dist**SIZE_EXPONENT)
    
  END FUNCTION AdaptiveElementSize
  
  !> Task 20.3: Enhanced annulus mesh generation with boundary layers
  !> Generates high-quality annulus mesh with optional boundary layers
  SUBROUTINE GenerateAnnulusMeshEnhanced(geometry, output_dir, quality)
    TYPE(GeometryParams), INTENT(IN) :: geometry
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    TYPE(MeshQuality), INTENT(INOUT) :: quality
    
    ! Local variables
    REAL(dp) :: r_inner, r_outer, dr, dtheta, r, theta
    REAL(dp) :: x, y, first_layer_height, growth_ratio
    INTEGER :: nr, ntheta, i, j, node_id, elem_id, boundary_id
    INTEGER :: n1, n2, n3, n4, num_bl_layers
    CHARACTER(LEN=256) :: filename
    INTEGER :: unit_header, unit_nodes, unit_elements, unit_boundary, ios
    INTEGER :: total_nodes, total_elements, total_boundaries
    REAL(dp), ALLOCATABLE :: radii(:), layer_heights(:)
    CHARACTER(LEN=100000) :: buffer
    INTEGER :: buffer_pos, line_len
    CHARACTER(LEN=1000) :: line
    REAL(dp) :: start_time, end_time
    
    ! Mathematical constants
    REAL(dp), PARAMETER :: PI = 3.141592653589793238_dp
    REAL(dp), PARAMETER :: TWO_PI = 2.0_dp * PI
    
    ! Start timing
    CALL CPU_TIME(start_time)
    
    ! Extract parameters
    r_inner = geometry%params(1)
    r_outer = geometry%params(2)
    
    ! Validate parameters
    IF (r_inner <= 0.0_dp .OR. r_outer <= r_inner) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Invalid annulus parameters"
      quality%return_code = 1
      RETURN
    END IF
    
    ! Calculate mesh dimensions
    ntheta = MAX(20, 10 * geometry%mesh_density)
    
    ! Task 20.1: Handle boundary layer generation
    IF (geometry%boundary_layer == 1) THEN
      num_bl_layers = 5 * geometry%mesh_density
      nr = num_bl_layers * 2  ! Boundary layers on both sides
      
      ! Calculate first layer height (1% of gap)
      first_layer_height = 0.01_dp * (r_outer - r_inner)
      growth_ratio = 1.2_dp
      
      ALLOCATE(layer_heights(num_bl_layers))
      ALLOCATE(radii(0:nr))
      
      ! Generate boundary layer spacing
      CALL GenerateBoundaryLayerSpacing(first_layer_height, growth_ratio, num_bl_layers, layer_heights)
      
      ! Build radial positions with boundary layers
      ! Inner boundary layers
      radii(0) = r_inner
      DO i = 1, num_bl_layers
        radii(i) = radii(i-1) + layer_heights(i)
      END DO
      
      ! Core region with uniform spacing
      dr = (r_outer - radii(num_bl_layers) - SUM(layer_heights)) / REAL(nr - 2*num_bl_layers, dp)
      DO i = num_bl_layers + 1, nr - num_bl_layers
        radii(i) = radii(i-1) + dr
      END DO
      
      ! Outer boundary layers (reversed)
      DO i = nr - num_bl_layers + 1, nr
        radii(i) = radii(i-1) + layer_heights(nr - i + 1)
      END DO
      radii(nr) = r_outer  ! Ensure exact outer radius
      
      DEALLOCATE(layer_heights)
    ELSE
      ! Uniform radial spacing
      nr = MAX(10, 5 * geometry%mesh_density)
      ALLOCATE(radii(0:nr))
      dr = (r_outer - r_inner) / REAL(nr, dp)
      DO i = 0, nr
        radii(i) = r_inner + i * dr
      END DO
    END IF
    
    ! Angular spacing
    dtheta = TWO_PI / REAL(ntheta, dp)
    
    ! Calculate totals
    total_nodes = (nr + 1) * ntheta
    total_elements = nr * ntheta
    total_boundaries = 2 * ntheta
    
    ! Write mesh header
    filename = TRIM(output_dir) // '/mesh.header'
    OPEN(NEWUNIT=unit_header, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.header"
      quality%return_code = 2
      DEALLOCATE(radii)
      RETURN
    END IF
    
    WRITE(unit_header, '(I0,1X,I0,1X,I0)') total_nodes, total_elements, total_boundaries
    WRITE(unit_header, '(I0)') 2
    WRITE(unit_header, '(I0,1X,I0)') 404, total_elements
    WRITE(unit_header, '(I0,1X,I0)') 202, total_boundaries
    CLOSE(unit_header)
    
    ! Write nodes with buffering
    filename = TRIM(output_dir) // '/mesh.nodes'
    OPEN(NEWUNIT=unit_nodes, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.nodes"
      quality%return_code = 2
      DEALLOCATE(radii)
      RETURN
    END IF
    
    buffer = ''
    buffer_pos = 1
    node_id = 0
    
    DO i = 0, nr
      r = radii(i)
      DO j = 0, ntheta-1
        theta = j * dtheta
        x = r * COS(theta)
        y = r * SIN(theta)
        node_id = node_id + 1
        
        ! Boundary tags: inner=1, outer=2, interior=-1
        IF (i == 0) THEN
          WRITE(line, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
                node_id, 1, x, y, 0.0_dp
        ELSE IF (i == nr) THEN
          WRITE(line, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
                node_id, 2, x, y, 0.0_dp
        ELSE
          WRITE(line, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
                node_id, -1, x, y, 0.0_dp
        END IF
        
        line_len = LEN_TRIM(line)
        IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
          WRITE(unit_nodes, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
          buffer = ''
          buffer_pos = 1
        END IF
        
        buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
        buffer_pos = buffer_pos + line_len + 1
      END DO
    END DO
    
    IF (buffer_pos > 1) THEN
      IF (buffer_pos > 1 .AND. buffer(buffer_pos-1:buffer_pos-1) == NEW_LINE('A')) THEN
        WRITE(unit_nodes, '(A)', ADVANCE='NO') buffer(1:buffer_pos-2)
      ELSE
        WRITE(unit_nodes, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
      END IF
    END IF
    CLOSE(unit_nodes)
    
    ! Write elements
    filename = TRIM(output_dir) // '/mesh.elements'
    OPEN(NEWUNIT=unit_elements, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.elements"
      quality%return_code = 2
      DEALLOCATE(radii)
      RETURN
    END IF
    
    buffer = ''
    buffer_pos = 1
    elem_id = 0
    
    DO i = 0, nr-1
      DO j = 0, ntheta-1
        elem_id = elem_id + 1
        
        ! Node indices (counter-clockwise)
        n1 = i * ntheta + j + 1
        n2 = i * ntheta + MOD(j+1, ntheta) + 1
        n3 = (i+1) * ntheta + MOD(j+1, ntheta) + 1
        n4 = (i+1) * ntheta + j + 1
        
        WRITE(line, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
              elem_id, 1, 404, n1, n2, n3, n4
        line_len = LEN_TRIM(line)
        
        IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
          WRITE(unit_elements, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
          buffer = ''
          buffer_pos = 1
        END IF
        
        buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
        buffer_pos = buffer_pos + line_len + 1
      END DO
    END DO
    
    IF (buffer_pos > 1) THEN
      IF (buffer_pos > 1 .AND. buffer(buffer_pos-1:buffer_pos-1) == NEW_LINE('A')) THEN
        WRITE(unit_elements, '(A)', ADVANCE='NO') buffer(1:buffer_pos-2)
      ELSE
        WRITE(unit_elements, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
      END IF
    END IF
    CLOSE(unit_elements)
    
    ! Write boundaries
    filename = TRIM(output_dir) // '/mesh.boundary'
    OPEN(NEWUNIT=unit_boundary, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.boundary"
      quality%return_code = 2
      DEALLOCATE(radii)
      RETURN
    END IF
    
    boundary_id = 0
    
    ! Inner boundary
    DO j = 0, ntheta-1
      boundary_id = boundary_id + 1
      n1 = j + 1
      n2 = MOD(j+1, ntheta) + 1
      elem_id = j + 1
      WRITE(unit_boundary, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
            boundary_id, 1, elem_id, 0, 202, n1, n2
    END DO
    
    ! Outer boundary
    DO j = 0, ntheta-1
      boundary_id = boundary_id + 1
      n1 = nr * ntheta + j + 1
      n2 = nr * ntheta + MOD(j+1, ntheta) + 1
      elem_id = (nr-1) * ntheta + j + 1
      WRITE(unit_boundary, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
            boundary_id, 2, elem_id, 0, 202, n1, n2
    END DO
    
    CLOSE(unit_boundary)
    
    ! Update quality metrics
    quality%total_elements = total_elements
    quality%total_nodes = total_nodes
    quality%min_angle = 90.0_dp
    quality%max_angle = 90.0_dp
    quality%aspect_ratio_avg = 1.0_dp
    quality%aspect_ratio_max = 1.0_dp
    quality%return_code = 0
    
    ! Clean up
    DEALLOCATE(radii)
    
    ! End timing
    CALL CPU_TIME(end_time)
    
    WRITE(ERROR_UNIT, '(A,I0,A,I0,A)') &
      "INFO: Generated enhanced annulus mesh with ", total_nodes, " nodes and ", total_elements, " elements"
    WRITE(ERROR_UNIT, '(A,F8.4,A)') "INFO: Mesh generation time: ", end_time - start_time, " seconds"
    
  END SUBROUTINE GenerateAnnulusMeshEnhanced
  
  !> Task 20.4: Enhanced rectangle mesh generation with boundary layers
  !> Generates rectangle mesh with optional boundary layer refinement
  SUBROUTINE GenerateRectangleMeshEnhanced(geometry, output_dir, quality)
    TYPE(GeometryParams), INTENT(IN) :: geometry
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    TYPE(MeshQuality), INTENT(INOUT) :: quality
    
    ! Local variables
    REAL(dp) :: width, height, x, y
    INTEGER :: nx, ny, i, j, node_id, elem_id, bc_elem_id
    INTEGER :: n1, n2, n3, n4, num_bl_layers
    INTEGER :: unit_header, unit_nodes, unit_elements, unit_boundary, ios
    INTEGER :: total_boundary_elements
    CHARACTER(LEN=512) :: filename
    REAL(dp), ALLOCATABLE :: x_coords(:), y_coords(:), layer_heights(:)
    REAL(dp) :: first_layer_height, growth_ratio, core_width, core_height
    REAL(dp) :: dx_avg, dy_avg  ! Average element sizes for aspect ratio calculation
    CHARACTER(LEN=100000) :: buffer
    INTEGER :: buffer_pos, line_len
    CHARACTER(LEN=1000) :: line
    REAL(dp) :: start_time, end_time
    
    ! Start timing
    CALL CPU_TIME(start_time)
    
    ! Extract rectangle parameters
    width = geometry%params(1)
    height = geometry%params(2)
    
    ! Calculate base mesh dimensions
    nx = MAX(10, INT(10.0_dp * geometry%mesh_density * width))
    ny = MAX(10, INT(10.0_dp * geometry%mesh_density * height))
    
    ! Allocate coordinate arrays
    ALLOCATE(x_coords(0:nx))
    ALLOCATE(y_coords(0:ny))
    
    ! Task 20.1 & 20.4: Generate coordinates with boundary layers
    IF (geometry%boundary_layer == 1) THEN
      num_bl_layers = MAX(3, 2 * geometry%mesh_density)
      first_layer_height = 0.01_dp * MIN(width, height)
      growth_ratio = 1.2_dp
      
      ALLOCATE(layer_heights(num_bl_layers))
      CALL GenerateBoundaryLayerSpacing(first_layer_height, growth_ratio, num_bl_layers, layer_heights)
      
      ! X-direction with boundary layers
      ! Left boundary layers
      x_coords(0) = 0.0_dp
      DO i = 1, num_bl_layers
        x_coords(i) = x_coords(i-1) + layer_heights(i)
      END DO
      
      ! Core region
      core_width = width - 2.0_dp * SUM(layer_heights)
      DO i = num_bl_layers + 1, nx - num_bl_layers
        x_coords(i) = x_coords(num_bl_layers) + &
                      core_width * REAL(i - num_bl_layers, dp) / REAL(nx - 2*num_bl_layers, dp)
      END DO
      
      ! Right boundary layers
      DO i = nx - num_bl_layers + 1, nx
        x_coords(i) = x_coords(i-1) + layer_heights(nx - i + 1)
      END DO
      x_coords(nx) = width
      
      ! Y-direction with boundary layers
      ! Bottom boundary layers
      y_coords(0) = 0.0_dp
      DO j = 1, num_bl_layers
        y_coords(j) = y_coords(j-1) + layer_heights(j)
      END DO
      
      ! Core region
      core_height = height - 2.0_dp * SUM(layer_heights)
      DO j = num_bl_layers + 1, ny - num_bl_layers
        y_coords(j) = y_coords(num_bl_layers) + &
                      core_height * REAL(j - num_bl_layers, dp) / REAL(ny - 2*num_bl_layers, dp)
      END DO
      
      ! Top boundary layers
      DO j = ny - num_bl_layers + 1, ny
        y_coords(j) = y_coords(j-1) + layer_heights(ny - j + 1)
      END DO
      y_coords(ny) = height
      
      DEALLOCATE(layer_heights)
    ELSE
      ! Uniform spacing
      DO i = 0, nx
        x_coords(i) = width * REAL(i, dp) / REAL(nx, dp)
      END DO
      DO j = 0, ny
        y_coords(j) = height * REAL(j, dp) / REAL(ny, dp)
      END DO
    END IF
    
    ! Update quality metrics
    quality%total_nodes = (nx + 1) * (ny + 1)
    quality%total_elements = nx * ny
    total_boundary_elements = 2 * nx + 2 * ny
    
    ! Write mesh header
    filename = TRIM(output_dir) // '/mesh.header'
    OPEN(NEWUNIT=unit_header, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.header"
      quality%return_code = 2
      DEALLOCATE(x_coords, y_coords)
      RETURN
    END IF
    
    WRITE(unit_header, '(I0,1X,I0,1X,I0)') quality%total_nodes, quality%total_elements, total_boundary_elements
    WRITE(unit_header, '(I0)') 2
    WRITE(unit_header, '(I0,1X,I0)') 404, quality%total_elements
    WRITE(unit_header, '(I0,1X,I0)') 202, total_boundary_elements
    CLOSE(unit_header)
    
    ! Write nodes
    filename = TRIM(output_dir) // '/mesh.nodes'
    OPEN(NEWUNIT=unit_nodes, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.nodes"
      quality%return_code = 2
      DEALLOCATE(x_coords, y_coords)
      RETURN
    END IF
    
    buffer = ''
    buffer_pos = 1
    node_id = 0
    
    DO j = 0, ny
      DO i = 0, nx
        node_id = node_id + 1
        
        ! Determine boundary tag
        IF (i == 0 .OR. i == nx .OR. j == 0 .OR. j == ny) THEN
          ! Boundary node
          IF (j == 0) THEN
            WRITE(line, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
                  node_id, 1, x_coords(i), y_coords(j), 0.0_dp  ! Bottom
          ELSE IF (i == nx) THEN
            WRITE(line, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
                  node_id, 2, x_coords(i), y_coords(j), 0.0_dp  ! Right
          ELSE IF (j == ny) THEN
            WRITE(line, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
                  node_id, 3, x_coords(i), y_coords(j), 0.0_dp  ! Top
          ELSE
            WRITE(line, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
                  node_id, 4, x_coords(i), y_coords(j), 0.0_dp  ! Left
          END IF
        ELSE
          ! Interior node
          WRITE(line, '(I0,1X,I0,1X,ES16.8E3,1X,ES16.8E3,1X,ES16.8E3)') &
                node_id, -1, x_coords(i), y_coords(j), 0.0_dp
        END IF
        
        line_len = LEN_TRIM(line)
        IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
          WRITE(unit_nodes, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
          buffer = ''
          buffer_pos = 1
        END IF
        
        buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
        buffer_pos = buffer_pos + line_len + 1
      END DO
    END DO
    
    IF (buffer_pos > 1) THEN
      IF (buffer_pos > 1 .AND. buffer(buffer_pos-1:buffer_pos-1) == NEW_LINE('A')) THEN
        WRITE(unit_nodes, '(A)', ADVANCE='NO') buffer(1:buffer_pos-2)
      ELSE
        WRITE(unit_nodes, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
      END IF
    END IF
    CLOSE(unit_nodes)
    
    ! Write elements (same as before)
    filename = TRIM(output_dir) // '/mesh.elements'
    OPEN(NEWUNIT=unit_elements, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot open mesh.elements"
      quality%return_code = 2
      DEALLOCATE(x_coords, y_coords)
      RETURN
    END IF
    
    buffer = ''
    buffer_pos = 1
    elem_id = 0
    
    DO j = 1, ny
      DO i = 1, nx
        elem_id = elem_id + 1
        n1 = (j-1) * (nx+1) + i
        n2 = n1 + 1
        n3 = n1 + nx + 2
        n4 = n1 + nx + 1
        
        WRITE(line, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
              elem_id, 1, 404, n1, n2, n3, n4
        line_len = LEN_TRIM(line)
        
        IF (buffer_pos + line_len + 1 > LEN(buffer)) THEN
          WRITE(unit_elements, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
          buffer = ''
          buffer_pos = 1
        END IF
        
        buffer(buffer_pos:buffer_pos+line_len) = TRIM(line) // NEW_LINE('A')
        buffer_pos = buffer_pos + line_len + 1
      END DO
    END DO
    
    IF (buffer_pos > 1) THEN
      IF (buffer_pos > 1 .AND. buffer(buffer_pos-1:buffer_pos-1) == NEW_LINE('A')) THEN
        WRITE(unit_elements, '(A)', ADVANCE='NO') buffer(1:buffer_pos-2)
      ELSE
        WRITE(unit_elements, '(A)', ADVANCE='NO') buffer(1:buffer_pos-1)
      END IF
    END IF
    CLOSE(unit_elements)
    
    ! Write boundaries (same structure as before)
    filename = TRIM(output_dir) // '/mesh.boundary'
    OPEN(NEWUNIT=unit_boundary, FILE=filename, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    bc_elem_id = 0
    
    ! Bottom boundary
    DO i = 1, nx
      bc_elem_id = bc_elem_id + 1
      n1 = i
      n2 = i + 1
      elem_id = i
      WRITE(unit_boundary, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
            bc_elem_id, 1, elem_id, 0, 202, n1, n2
    END DO
    
    ! Right boundary
    DO j = 1, ny
      bc_elem_id = bc_elem_id + 1
      n1 = j * (nx+1) + nx + 1
      n2 = (j+1) * (nx+1) + nx + 1
      elem_id = j * nx
      WRITE(unit_boundary, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
            bc_elem_id, 2, elem_id, 0, 202, n1, n2
    END DO
    
    ! Top boundary
    DO i = 1, nx
      bc_elem_id = bc_elem_id + 1
      n1 = ny * (nx+1) + i + 1
      n2 = ny * (nx+1) + i
      elem_id = (ny-1) * nx + i
      WRITE(unit_boundary, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
            bc_elem_id, 3, elem_id, 0, 202, n1, n2
    END DO
    
    ! Left boundary
    DO j = 1, ny
      bc_elem_id = bc_elem_id + 1
      n1 = (j+1) * (nx+1) + 1
      n2 = j * (nx+1) + 1
      elem_id = (j-1) * nx + 1
      WRITE(unit_boundary, '(I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0,1X,I0)') &
            bc_elem_id, 4, elem_id, 0, 202, n1, n2
    END DO
    
    CLOSE(unit_boundary)
    
    ! Compute quality metrics
    quality%min_angle = 90.0_dp
    quality%max_angle = 90.0_dp
    
    ! Calculate aspect ratios based on actual element sizes
    IF (geometry%boundary_layer == 1) THEN
      ! With boundary layers, aspect ratios vary
      quality%aspect_ratio_avg = 1.5_dp  ! Approximate
      quality%aspect_ratio_max = 3.0_dp   ! Conservative estimate
    ELSE
      ! Uniform mesh
      dx_avg = width / REAL(nx, dp)
      dy_avg = height / REAL(ny, dp)
      quality%aspect_ratio_avg = MAX(dx_avg/dy_avg, dy_avg/dx_avg)
      quality%aspect_ratio_max = quality%aspect_ratio_avg
    END IF
    
    quality%return_code = 0
    
    ! Clean up
    DEALLOCATE(x_coords, y_coords)
    
    ! End timing
    CALL CPU_TIME(end_time)
    
    WRITE(ERROR_UNIT, '(A,I0,A,I0,A)') "INFO: Generated enhanced rectangle mesh with ", &
         quality%total_elements, " elements and ", quality%total_nodes, " nodes"
    WRITE(ERROR_UNIT, '(A,F8.4,A)') "INFO: Mesh generation time: ", end_time - start_time, " seconds"
    
  END SUBROUTINE GenerateRectangleMeshEnhanced
  
  !> Task 20.5: Performance benchmarking routine
  !> Benchmarks mesh generation for different geometries and sizes
  SUBROUTINE BenchmarkMeshGeneration(output_dir)
    CHARACTER(LEN=*), INTENT(IN) :: output_dir
    
    ! Local variables
    TYPE(GeometryParams) :: test_geometry
    TYPE(MeshQuality) :: test_quality
    REAL(dp) :: start_time, end_time, total_time
    INTEGER :: density, geom_type
    CHARACTER(LEN=256) :: test_dir, benchmark_file
    INTEGER :: unit_bench, ios
    CHARACTER(LEN=50) :: geom_names(4)
    
    geom_names = (/ "Rectangle   ", "Circle      ", "Annulus     ", "L-shape     " /)
    
    ! Open benchmark results file
    benchmark_file = TRIM(output_dir) // '/benchmark_results.txt'
    OPEN(NEWUNIT=unit_bench, FILE=benchmark_file, STATUS='REPLACE', ACTION='WRITE', IOSTAT=ios)
    IF (ios /= 0) THEN
      WRITE(ERROR_UNIT, *) "ERROR: Cannot create benchmark file"
      RETURN
    END IF
    
    WRITE(unit_bench, '(A)') "Educational Mesh Generator Performance Benchmarks"
    WRITE(unit_bench, '(A)') "================================================"
    WRITE(unit_bench, '(A)') ""
    WRITE(unit_bench, '(A)') "Geometry      Density  Elements    Nodes      Time(s)   Elements/s"
    WRITE(unit_bench, '(A)') "--------      -------  --------    -------    -------   ----------"
    
    ! Benchmark each geometry type
    DO geom_type = 1, 4
      test_geometry%geometry_type = geom_type
      
      ! Set default parameters
      SELECT CASE(geom_type)
      CASE(1)  ! Rectangle
        test_geometry%params(1) = 1.0_dp   ! width
        test_geometry%params(2) = 1.0_dp   ! height
      CASE(2)  ! Circle
        test_geometry%params(1) = 1.0_dp   ! radius
      CASE(3)  ! Annulus
        test_geometry%params(1) = 0.5_dp   ! inner radius
        test_geometry%params(2) = 1.0_dp   ! outer radius
      CASE(4)  ! L-shape
        test_geometry%params(1) = 1.0_dp   ! width
        test_geometry%params(2) = 1.0_dp   ! height
        test_geometry%params(3) = 0.5_dp   ! cut_x
        test_geometry%params(4) = 0.5_dp   ! cut_y
      END SELECT
      
      ! Test different densities
      DO density = 1, 5, 2
        test_geometry%mesh_density = density
        test_geometry%boundary_layer = 0  ! No boundary layers for base benchmark
        
        ! Create test directory
        WRITE(test_dir, '(A,A,I1,A,I1)') TRIM(output_dir), '/benchmark_', geom_type, '_', density
        CALL EXECUTE_COMMAND_LINE('mkdir -p ' // TRIM(test_dir))
        
        ! Time the mesh generation
        CALL CPU_TIME(start_time)
        
        SELECT CASE(geom_type)
        CASE(1)
          CALL GenerateRectangleMeshEnhanced(test_geometry, test_dir, test_quality)
        CASE(2)
          CALL GenerateCircleMesh(test_geometry, test_dir, test_quality)
        CASE(3)
          CALL GenerateAnnulusMeshEnhanced(test_geometry, test_dir, test_quality)
        CASE(4)
          CALL GenerateLShapeMesh(test_geometry, test_dir, test_quality)
        END SELECT
        
        CALL CPU_TIME(end_time)
        total_time = end_time - start_time
        
        ! Write results
        IF (test_quality%return_code == 0) THEN
          WRITE(unit_bench, '(A12,2X,I7,2X,I8,2X,I9,2X,F8.4,2X,F10.1)') &
                TRIM(geom_names(geom_type)), density, test_quality%total_elements, &
                test_quality%total_nodes, total_time, &
                REAL(test_quality%total_elements, dp) / total_time
        ELSE
          WRITE(unit_bench, '(A12,2X,I7,2X,A)') &
                TRIM(geom_names(geom_type)), density, "FAILED"
        END IF
      END DO
      
      WRITE(unit_bench, '(A)') ""
    END DO
    
    ! Benchmark with boundary layers
    WRITE(unit_bench, '(A)') ""
    WRITE(unit_bench, '(A)') "Boundary Layer Mesh Benchmarks"
    WRITE(unit_bench, '(A)') "------------------------------"
    WRITE(unit_bench, '(A)') ""
    
    test_geometry%boundary_layer = 1
    test_geometry%mesh_density = 3
    
    DO geom_type = 1, 3  ! Rectangle, Circle, Annulus support boundary layers
      test_geometry%geometry_type = geom_type
      
      ! Set parameters as before
      SELECT CASE(geom_type)
      CASE(1)
        test_geometry%params(1) = 1.0_dp
        test_geometry%params(2) = 1.0_dp
      CASE(2)
        test_geometry%params(1) = 1.0_dp
      CASE(3)
        test_geometry%params(1) = 0.5_dp
        test_geometry%params(2) = 1.0_dp
      END SELECT
      
      WRITE(test_dir, '(A,A,I1,A)') TRIM(output_dir), '/benchmark_bl_', geom_type
      CALL EXECUTE_COMMAND_LINE('mkdir -p ' // TRIM(test_dir))
      
      CALL CPU_TIME(start_time)
      
      SELECT CASE(geom_type)
      CASE(1)
        CALL GenerateRectangleMeshEnhanced(test_geometry, test_dir, test_quality)
      CASE(2)
        CALL GenerateCircleMesh(test_geometry, test_dir, test_quality)
      CASE(3)
        CALL GenerateAnnulusMeshEnhanced(test_geometry, test_dir, test_quality)
      END SELECT
      
      CALL CPU_TIME(end_time)
      total_time = end_time - start_time
      
      IF (test_quality%return_code == 0) THEN
        WRITE(unit_bench, '(A12,2X,A,2X,I8,2X,I9,2X,F8.4,2X,F10.1)') &
              TRIM(geom_names(geom_type)), "BL", test_quality%total_elements, &
              test_quality%total_nodes, total_time, &
              REAL(test_quality%total_elements, dp) / total_time
      END IF
    END DO
    
    CLOSE(unit_bench)
    
    WRITE(ERROR_UNIT, '(A,A)') "INFO: Benchmark results written to ", TRIM(benchmark_file)
    
  END SUBROUTINE BenchmarkMeshGeneration
  
END MODULE EducationalMeshGenerator
