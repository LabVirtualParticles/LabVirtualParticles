#----------------------------------------------------------------------------
# B3a adaptado para o Geantino Labs (modo batch, sem parte grafica).
# Baseado no CMakeLists.txt do examples/basic/B3/B3a da Colaboracao Geant4.
#
cmake_minimum_required(VERSION 3.16...3.27)
project(GeantinoB3a)

# Sem ui_all/vis_all: este programa nao abre interface nem visualizacao,
# entao compila igual num Geant4 sem Qt/OpenGL (como o do servidor).
# Precisa do Geant4 compilado com GDML (GEANT4_USE_GDML=ON).
find_package(Geant4 REQUIRED)

file(GLOB sources ${PROJECT_SOURCE_DIR}/src/*.cc)
file(GLOB headers ${PROJECT_SOURCE_DIR}/include/*.hh)

add_executable(geantinoB3a geantinoB3a.cc ${sources} ${headers})
target_include_directories(geantinoB3a PRIVATE include)
target_link_libraries(geantinoB3a PRIVATE ${Geant4_LIBRARIES})

# Copia as macros para a pasta de build, para testar com ./geantinoB3a
foreach(_script run_batch_exemplo.mac)
  configure_file(
    ${PROJECT_SOURCE_DIR}/macros/${_script}
    ${PROJECT_BINARY_DIR}/${_script}
    COPYONLY
    )
endforeach()
