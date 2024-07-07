#--------------------------------------------------------
# The CMakeLists.txt for:                       pAhoiLocSolution
# Author(s):                              Daniel Duecker
#--------------------------------------------------------

find_package(MOOS REQUIRED)
find_package(Armadillo REQUIRED)
find_package(BLAS REQUIRED)
find_package(LAPACK REQUIRED)

include_directories(${MOOS_INCLUDE_DIRS})
include_directories(${ARMADILLO_INCLUDE_DIRS})


SET(SRC
  AhoiLocSolution.cpp
  AhoiLocSolution_Info.cpp
  RangingLocEKF.cpp
  main.cpp
)


ADD_EXECUTABLE(pAhoiLocSolution ${SRC})

TARGET_LINK_LIBRARIES(pAhoiLocSolution
   ${MOOS_LIBRARIES}
   apputil
   mbutil
   m
   pthread
   ${ARMADILLO_LIBRARIES}
   ${BLAS_LIBRARIES}
   ${LAPACK_LIBRARIES}
   )

